import asyncio
from telethon import TelegramClient, events
from telethon.tl.types import PeerUser, PeerChat, PeerChannel
import os
import re
import time

# Параметры передаются при создании экземпляра класса

def extract_response_from_analysis(analysis_text):
    """Извлечь предложенный ответ из анализа ИИ"""
    lines = analysis_text.split('\n')
    response_started = False
    response_lines = []

    for line in lines:
        # Ищем строку, которая начинается с "Ответ:" (может быть в markdown)
        if 'Ответ:' in line:
            response_started = True
            # Берем все после "Ответ:"
            response_part = line.split('Ответ:', 1)[1].strip()
            # Убираем markdown звездочки и ---
            response_part = response_part.replace('**', '').replace('---', '').strip()
            if response_part:
                response_lines.append(response_part)
            continue

        # Если начали собирать ответ
        if response_started:
            # Останавливаемся при встрече закрывающих тегов или новых секций
            if (line.strip() == '---' or
                line.startswith('```') or
                line.strip().startswith('```') or
                'Фаза:' in line or
                'Тип:' in line or
                'Контекст:' in line):
                break

            # Убираем markdown символы и добавляем строку (даже пустые для сохранения структуры)
            clean_line = line.replace('**', '').replace('*', '')
            response_lines.append(clean_line)

    if response_lines:
        # Соединяем строки с переносами, убираем лишние пробелы в начале и конце
        full_response = '\n'.join(response_lines).strip()

        # Убираем проблематичные испанские символы
        full_response = full_response.replace('¿', '').replace('¡', '')

        return full_response
    return None

class TelegramReader:
    def __init__(self, api_id, api_hash, phone_number):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        self.client = TelegramClient('sessions/session', api_id, api_hash)
        self.new_message_handler = None
        self.ai_client = None
        self.system_prompt = ""
        self.model = ""
        self.kb_retriever = None  # RAG retriever
        self.ui_callback = None

    async def connect(self):
        """Подключение к Telegram"""
        await self.client.start(phone=self.phone_number)
        print("Подключен к Telegram")

    async def get_all_dialogs(self):
        """Получить все диалоги пользователя"""
        dialogs = []
        async for dialog in self.client.iter_dialogs():
            dialogs.append({
                'id': dialog.id,
                'name': dialog.name,
                'entity': dialog.entity,
                'is_user': dialog.is_user,
                'is_group': dialog.is_group,
                'is_channel': dialog.is_channel
            })
        return dialogs

    async def get_last_messages(self, dialog_entity, limit=15):
        """Получить последние N сообщений из диалога"""
        messages = []
        try:
            async for message in self.client.iter_messages(dialog_entity, limit=limit):
                if message.text:  # Только текстовые сообщения
                    messages.append({
                        'id': message.id,
                        'date': message.date,
                        'text': message.text,
                        'sender_id': message.sender_id,
                        'is_outgoing': message.out
                    })
        except Exception as e:
            print(f"Ошибка при получении сообщений: {e}")

        return messages[::-1]  # Возвращаем в хронологическом порядке

    async def get_dialog_context(self, dialog_name=None, dialog_id=None, message_limit=15):
        """Получить контекст диалога по имени или ID"""
        dialogs = await self.get_all_dialogs()

        target_dialog = None
        if dialog_name:
            target_dialog = next((d for d in dialogs if dialog_name.lower() in d['name'].lower()), None)
        elif dialog_id:
            target_dialog = next((d for d in dialogs if d['id'] == dialog_id), None)

        if not target_dialog:
            return None

        messages = await self.get_last_messages(target_dialog['entity'], message_limit)

        return {
            'dialog': target_dialog,
            'messages': messages,
            'formatted_context': self.format_messages_for_analysis(messages)
        }

    async def find_dialog_by_input(self, user_input):
        """Найти диалог по имени или UserID"""
        dialogs = await self.get_all_dialogs()

        # Проверяем, является ли ввод числом (UserID)
        try:
            user_id = int(user_input)
            # Ищем по ID
            target_dialog = next((d for d in dialogs if d['id'] == user_id), None)
            if target_dialog:
                return target_dialog
        except ValueError:
            pass

        # Ищем по имени (частичное совпадение, без учета регистра)
        user_input_lower = user_input.lower()
        target_dialog = next((d for d in dialogs if user_input_lower in d['name'].lower()), None)

        return target_dialog

    async def get_dialogs_list(self, limit=10):
        """Получить список первых N диалогов с ID и именами"""
        dialogs = await self.get_all_dialogs()

        result = []
        for i, dialog in enumerate(dialogs[:limit]):
            result.append({
                'index': i + 1,
                'id': dialog['id'],
                'name': dialog['name'],
                'type': 'Пользователь' if dialog['is_user'] else ('Группа' if dialog['is_group'] else 'Канал')
            })

        return result

    def format_messages_for_analysis(self, messages):
        """Форматировать сообщения для анализа ИИ"""
        formatted = []
        for msg in messages:
            sender = "Я" if msg['is_outgoing'] else "Собеседник"
            formatted.append(f"{sender}: {msg['text']}")

        return "\n".join(formatted)

    async def get_all_dialogs_with_context(self, message_limit=15):
        """Получить все диалоги с контекстом последних сообщений"""
        dialogs = await self.get_all_dialogs()
        dialogs_with_context = []

        for dialog in dialogs:
            if dialog['is_user']:  # Только личные диалоги
                messages = await self.get_last_messages(dialog['entity'], message_limit)
                if messages:  # Только если есть сообщения
                    dialogs_with_context.append({
                        'dialog': dialog,
                        'messages': messages,
                        'formatted_context': self.format_messages_for_analysis(messages)
                    })

        return dialogs_with_context

    async def analyze_dialog_with_ai(self, dialog_name=None, dialog_id=None, message_limit=15, ai_client=None, system_prompt="", model=""):
        """Анализ диалога с помощью ИИ"""
        if not ai_client:
            raise ValueError("Необходимо передать ai_client для анализа")

        # Получаем контекст диалога
        dialog_context = await self.get_dialog_context(dialog_name=dialog_name, dialog_id=dialog_id, message_limit=message_limit)

        if not dialog_context:
            return None

        # Форматируем сообщения для анализа
        lead_dialogue = dialog_context['formatted_context']

        # Отправляем на анализ в ИИ
        chat_response = ai_client.chat.complete(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": lead_dialogue
                }
            ]
        )

        analysis_result = chat_response.choices[0].message.content

        return {
            'dialog_name': dialog_context['dialog']['name'],
            'dialog_id': dialog_context['dialog']['id'],
            'messages': dialog_context['messages'],
            'formatted_context': lead_dialogue,
            'analysis': analysis_result
        }

    async def analyze_all_dialogs_with_ai(self, message_limit=15, ai_client=None, system_prompt="", model=""):
        """Анализ всех диалогов с помощью ИИ"""
        if not ai_client:
            raise ValueError("Необходимо передать ai_client для анализа")

        # Получаем все диалоги с контекстом
        dialogs_with_context = await self.get_all_dialogs_with_context(message_limit)

        results = []

        for dialog_data in dialogs_with_context:
            dialog = dialog_data['dialog']
            lead_dialogue = dialog_data['formatted_context']

            # Анализируем каждый диалог
            chat_response = ai_client.chat.complete(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": lead_dialogue
                    }
                ]
            )

            analysis_result = chat_response.choices[0].message.content

            results.append({
                'dialog_name': dialog['name'],
                'dialog_id': dialog['id'],
                'messages_count': len(dialog_data['messages']),
                'formatted_context': lead_dialogue,
                'analysis': analysis_result
            })

        return results

    async def send_message(self, dialog_id, message_text):
        """Отправить сообщение в диалог"""
        try:
            await self.client.send_message(dialog_id, message_text)
            return True
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {e}")
            return False

    async def mark_dialog_as_read(self, dialog_entity):
        """Отметить диалог как прочитанный в Telegram"""
        try:
            # Отмечаем все сообщения в диалоге как прочитанные
            await self.client.send_read_acknowledge(dialog_entity)
            print(f"✅ Диалог отмечен как прочитанный в Telegram")
            return True
        except Exception as e:
            print(f"❌ Ошибка отметки диалога как прочитанного: {e}")
            return False

    def is_spanish_text(self, text):
        """Определяет, является ли текст испанским"""
        if not text:
            return False

        # Характерные испанские слова и фразы
        spanish_indicators = [
            'hola', 'buenas', 'gracias', 'muchas gracias', 'de nada', 'por favor',
            'claro', 'perfecto', 'excelente', 'bueno', 'muy bien', 'está bien',
            'quiero', 'necesito', 'puedo', 'tienes', 'tengo', 'estoy', 'soy',
            'dinero', 'depositar', 'retiro', 'cuenta', 'banco', 'trading',
            'inversión', 'ganancia', 'beneficio', 'pérdida', 'mercado',
            'comprendo', 'entiendo', 'perfecto', 'cuando', 'donde', 'como',
            'qué', 'cuánto', 'cuándo', 'dónde', 'cómo', 'cuál',
            'señor', 'señora', 'amigo', 'cliente', 'asesor', 'bien', 'si', 'sí',
            'no', 'que', 'muy', 'poco', 'mucho', 'todo', 'nada', 'algo',
            'este', 'esta', 'esto', 'ese', 'esa', 'eso', 'aquel', 'aquella',
            'con', 'sin', 'para', 'por', 'hasta', 'desde', 'entre', 'sobre', 'pf', 'q'
        ]

        # Характерные буквы и символы испанского
        spanish_chars = ['ñ', 'á', 'é', 'í', 'ó', 'ú', '¿', '¡']

        text_lower = text.lower().strip()

        # Проверяем наличие испанских символов (высокий приоритет)
        spanish_char_count = sum(1 for char in spanish_chars if char in text_lower)
        if spanish_char_count > 0:
            return True

        # Проверяем наличие испанских слов
        # Разбиваем на слова и проверяем точные совпадения
        words = re.findall(r'\w+', text_lower)
        spanish_word_count = sum(1 for word in words if word in spanish_indicators)

        # Для коротких сообщений (1-3 слова) достаточно одного испанского слова
        if len(words) <= 3 and spanish_word_count >= 1:
            return True

        # Для длинных сообщений нужно больше испанских слов
        return spanish_word_count >= 2

    async def is_lead_dialog(self, dialog_entity, message_limit=10):
        """Определяет, является ли диалог лидом (переписка на испанском)"""
        try:
            messages = await self.get_last_messages(dialog_entity, message_limit)
            if not messages:
                return False

            # Сначала проверяем последние 3 сообщения (приоритет недавним)
            recent_messages = messages[-3:] if len(messages) >= 3 else messages
            spanish_recent = 0
            total_recent = 0

            for message in recent_messages:
                if message['text'] and len(message['text'].strip()) > 2:
                    total_recent += 1
                    if self.is_spanish_text(message['text']):
                        spanish_recent += 1

            # Если последние сообщения на испанском (приоритет)
            if total_recent > 0 and spanish_recent / total_recent >= 0.5:
                return True

            # Если недавних испанских мало, проверяем все сообщения
            spanish_messages = 0
            total_text_messages = 0

            for message in messages:
                if message['text'] and len(message['text'].strip()) > 5:
                    total_text_messages += 1
                    if self.is_spanish_text(message['text']):
                        spanish_messages += 1

            # Если больше 30% сообщений на испанском (снизили порог)
            if total_text_messages > 0:
                spanish_ratio = spanish_messages / total_text_messages
                return spanish_ratio > 0.3

            return False
        except Exception as e:
            print(f"Ошибка при проверке диалога на испанский: {e}")
            return False

    async def get_leads_only(self, message_limit=10):
        """Получить только диалоги с лидами (испанская переписка)"""
        dialogs = await self.get_all_dialogs()
        leads = []

        for dialog in dialogs:
            if dialog['is_user']:  # Только личные диалоги
                if await self.is_lead_dialog(dialog['entity'], message_limit):
                    messages = await self.get_last_messages(dialog['entity'], message_limit)
                    if messages:
                        leads.append({
                            'dialog': dialog,
                            'messages': messages,
                            'formatted_context': self.format_messages_for_analysis(messages)
                        })

        return leads

    async def dialog_needs_response(self, dialog_entity):
        """Проверяет, нужно ли отвечать в диалоге (последнее сообщение не от нас)"""
        try:
            messages = await self.get_last_messages(dialog_entity, 1)
            if messages:
                last_message = messages[0]
                return not last_message['is_outgoing']  # True если последнее сообщение НЕ от нас
            return False
        except Exception as e:
            print(f"Ошибка при проверке необходимости ответа: {e}")
            return False

    async def get_unread_leads(self):
        """Получить лидов, которым нужно ответить"""
        leads = await self.get_leads_only()
        unread_leads = []

        for lead in leads:
            if await self.dialog_needs_response(lead['dialog']['entity']):
                unread_leads.append(lead)

        return unread_leads

    async def setup_auto_responder(self, ai_client, system_prompt, model, ui_callback=None, kb_retriever=None):
        """Настроить автоответчик с ИИ"""
        self.ai_client = ai_client
        self.system_prompt = system_prompt
        self.model = model
        self.ui_callback = ui_callback
        self.kb_retriever = kb_retriever  # RAG retriever

        @self.client.on(events.NewMessage(incoming=True))
        async def handle_new_message(event):
            try:
                # Проверяем, что это личное сообщение
                if not event.is_private:
                    return

                sender = await event.get_sender()
                dialog_entity = await event.get_chat()

                print(f"\n📩 Новое сообщение от {sender.first_name if sender.first_name else 'Unknown'} ({sender.id})")
                print(f"Текст: {event.message.text}")

                # Проверяем, является ли этот диалог лидом
                print(f"🔍 Проверяем текст '{event.message.text}' на испанский...")
                is_spanish = self.is_spanish_text(event.message.text)
                print(f"📝 Сообщение испанское: {is_spanish}")

                is_lead = await self.is_lead_dialog(dialog_entity)
                print(f"🎯 Диалог является лидом: {is_lead}")

                if is_lead:
                    print("✅ Это лид! Анализируем...")

                    # Получаем контекст диалога
                    messages = await self.get_last_messages(dialog_entity, 10)
                    if messages:
                        formatted_context = self.format_messages_for_analysis(messages)

                        # Анализируем с помощью ИИ
                        analysis_result = await self.get_ai_response(formatted_context)

                        if analysis_result:
                            print(f"📊 Анализ ИИ:\n{analysis_result}")

                            # Извлекаем ответ из анализа
                            response = extract_response_from_analysis(analysis_result)

                            if response:
                                print(f"🤖 Извлеченный ответ: {response}")

                                # Отправляем ответ
                                success = await self.send_message(dialog_entity, response)
                                if success:
                                    print("✅ Ответ отправлен!")

                                    # Отмечаем диалог как прочитанный в Telegram
                                    print("📖 Отмечаем диалог как прочитанный...")
                                    read_success = await self.mark_dialog_as_read(dialog_entity)
                                    if read_success:
                                        print("✅ Диалог отмечен как прочитанный в Telegram")
                                    else:
                                        print("⚠️ Не удалось отметить диалог как прочитанный")

                                    # Вызываем callback для обновления UI
                                    if self.ui_callback:
                                        sender_name = getattr(sender, 'first_name', 'Неизвестно')
                                        if hasattr(sender, 'last_name') and sender.last_name:
                                            sender_name += f" {sender.last_name}"

                                        try:
                                            await self.ui_callback(dialog_entity, response, sender_name)
                                        except Exception as callback_error:
                                            print(f"❌ Ошибка в UI callback: {callback_error}")
                                else:
                                    print("❌ Ошибка при отправке ответа")
                            else:
                                print("❌ Не удалось извлечь ответ из анализа")
                        else:
                            print("❌ Не удалось получить ответ от ИИ")
                else:
                    print("ℹ️ Это не лид, пропускаем")

            except Exception as e:
                print(f"❌ Ошибка в обработчике сообщений: {e}")

    async def get_ai_response(self, formatted_context):
        """Получить ответ от ИИ с использованием RAG"""
        try:
            # Если есть retriever, используем RAG
            if self.kb_retriever:
                print("🔍 Поиск релевантных документов в KB...")

                # Получаем релевантные документы
                retrieved_docs = self.kb_retriever.retrieve(formatted_context, top_k=3)

                if retrieved_docs:
                    print(f"📚 Найдено {len(retrieved_docs)} релевантных документов")

                    # Форматируем контекст из KB
                    kb_context = self.kb_retriever.format_retrieved_context(retrieved_docs)

                    # Добавляем KB контекст в промпт пользователя
                    user_content = f"""Документы из базы знаний:

{kb_context}

---

Диалог с клиентом:
{formatted_context}"""
                else:
                    print("⚠️ Релевантные документы не найдены, используем только диалог")
                    user_content = formatted_context
            else:
                # Без retriever используем обычный режим
                user_content = formatted_context

            chat_response = self.ai_client.chat.complete(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_content
                    }
                ]
            )

            return chat_response.choices[0].message.content
        except Exception as e:
            print(f"Ошибка при получении ответа от ИИ: {e}")
            return None

    async def process_existing_unread_leads(self):
        """Обработать существующие непрочитанные сообщения от лидов"""
        print("🔍 Проверяем существующие непрочитанные сообщения...")

        unread_leads = await self.get_unread_leads()

        if not unread_leads:
            print("✅ Нет непрочитанных сообщений от лидов")
            return

        print(f"📋 Найдено {len(unread_leads)} лидов, которым нужно ответить")

        for lead in unread_leads:
            try:
                dialog = lead['dialog']
                print(f"\n💬 Обрабатываем диалог с {dialog['name']} (ID: {dialog['id']})")

                # Получаем ответ от ИИ
                analysis_result = await self.get_ai_response(lead['formatted_context'])

                if analysis_result:
                    print(f"📊 Анализ ИИ:\n{analysis_result}")

                    # Извлекаем ответ из анализа
                    response = extract_response_from_analysis(analysis_result)

                    if response:
                        print(f"🤖 Извлеченный ответ: {response}")

                        # Отправляем ответ
                        success = await self.send_message(dialog['entity'], response)
                        if success:
                            print("✅ Ответ отправлен!")
                            time.sleep(2)  # Пауза между отправками
                        else:
                            print("❌ Ошибка при отправке ответа")
                    else:
                        print("❌ Не удалось извлечь ответ из анализа")
                else:
                    print("❌ Не удалось получить ответ от ИИ")

            except Exception as e:
                print(f"❌ Ошибка при обработке лида {dialog['name']}: {e}")

    async def start_monitoring(self):
        """Запустить мониторинг новых сообщений"""
        print("🚀 Запуск мониторинга новых сообщений...")
        print("💡 Для остановки нажмите Ctrl+C")

        # Сначала обрабатываем существующие непрочитанные
        await self.process_existing_unread_leads()

        print("\n👀 Ожидаем новые сообщения...")

        # Запускаем мониторинг
        await self.client.run_until_disconnected()

    async def close(self):
        """Закрыть соединение"""
        await self.client.disconnect()

# Пример использования
async def main():
    # Импортируем настройки из settings.py
    from config.settings import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE

    telegram = TelegramReader(TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE)

    try:
        await telegram.connect()

        # Получить все диалоги с контекстом
        dialogs_with_context = await telegram.get_all_dialogs_with_context(15)

        print(f"Найдено {len(dialogs_with_context)} диалогов с сообщениями")

        # Пример обработки каждого диалога
        for dialog_data in dialogs_with_context:
            dialog = dialog_data['dialog']
            context = dialog_data['formatted_context']

            print(f"\n=== Диалог с {dialog['name']} ===")
            print(f"Последние сообщения:\n{context}")
            print("-" * 50)

    finally:
        await telegram.close()

if __name__ == '__main__':
    asyncio.run(main())