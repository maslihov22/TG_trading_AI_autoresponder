#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

"""

import flet as ft
import asyncio
import threading
import time
from datetime import datetime
from mistralai import Mistral
from core.telegram_client import TelegramReader, extract_response_from_analysis
from config.settings import *

class SantiagoUI:
    def __init__(self):
        self.telegram_reader = None
        self.ai_client = None
        self.auto_responder_active = False
        self.dialogs = []
        self.selected_dialog = None
        self.stats = {"leads": 0, "processed": 0, "responses_sent": 0}
        self.notification_container = None
        self.message_listener_active = False

    async def main(self, page: ft.Page):
        self.page = page  # Сохраняем ссылку на страницу
        page.title = "AI Telegram Assistant"
        page.theme_mode = "dark"
        page.window_width = 1200
        page.window_height = 800
        page.window_min_width = 800
        page.window_min_height = 600

        # Цветовая схема
        primary_color = ft.Colors.BLUE_600
        success_color = ft.Colors.GREEN_600
        warning_color = ft.Colors.ORANGE_600
        error_color = ft.Colors.RED_600

        # Состояние соединения
        self.connection_status = ft.Text("❌ Не подключен", color=error_color, size=14)
        self.auto_responder_status = ft.Text("⏸️ Неактивен", color=warning_color, size=14)

        # Статистика
        self.stats_leads = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=primary_color)
        self.stats_processed = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=success_color)
        self.stats_responses = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color=warning_color)

        # Список диалогов
        self.dialogs_list = ft.ListView(expand=1, spacing=10, padding=20)

        # Панель анализа
        self.analysis_panel = ft.Container(
            content=ft.Column([
                ft.Text("Выберите диалог для анализа", size=16, color=ft.Colors.GREY_400)
            ]),
            padding=20,
            border_radius=10,
            bgcolor=ft.Colors.GREY_900,
            expand=True
        )

        # Кнопки управления
        async def connect_clicked(e):
            await self.connect_to_telegram()

        async def toggle_auto_responder(e):
            await self.toggle_auto_responder()

        async def refresh_dialogs(e):
            await self.load_dialogs()

        async def analyze_selected(e):
            if self.selected_dialog:
                await self.analyze_dialog(self.selected_dialog)

        connect_btn = ft.ElevatedButton(
            "🔗 Подключиться к Telegram",
            on_click=connect_clicked,
            style=ft.ButtonStyle(
                bgcolor=primary_color,
                color=ft.Colors.WHITE,
                padding=ft.padding.all(15)
            )
        )

        auto_responder_btn = ft.ElevatedButton(
            "▶️ Запустить Авто-Ответчик",
            on_click=toggle_auto_responder,
            style=ft.ButtonStyle(
                bgcolor=success_color,
                color=ft.Colors.WHITE,
                padding=ft.padding.all(15)
            )
        )

        refresh_btn = ft.ElevatedButton(
            "🔄 Обновить диалоги",
            on_click=refresh_dialogs,
            style=ft.ButtonStyle(
                bgcolor=warning_color,
                color=ft.Colors.WHITE,
                padding=ft.padding.all(10)
            )
        )

        # Верхняя панель статуса
        status_row = ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text("Статус подключения", size=12, color=ft.Colors.GREY_400),
                    self.connection_status
                ]),
                padding=10
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Авто-ответчик", size=12, color=ft.Colors.GREY_400),
                    self.auto_responder_status
                ]),
                padding=10
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Лиды", size=12, color=ft.Colors.GREY_400),
                    self.stats_leads
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=10
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Обработано", size=12, color=ft.Colors.GREY_400),
                    self.stats_processed
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=10
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Отправлено", size=12, color=ft.Colors.GREY_400),
                    self.stats_responses
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=10
            )
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

        # Кнопки управления
        controls_row = ft.Row([
            connect_btn,
            auto_responder_btn,
            refresh_btn
        ], alignment=ft.MainAxisAlignment.START, spacing=10)

        # Основной контент
        main_content = ft.Row([
            # Левая панель - список диалогов
            ft.Container(
                content=ft.Column([
                    ft.Text("📋 Диалоги", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self.dialogs_list
                ]),
                width=400,
                padding=20,
                border_radius=10,
                bgcolor=ft.Colors.GREY_900,
                expand=False
            ),
            # Правая панель - анализ
            ft.Container(
                content=ft.Column([
                    ft.Text("🔍 Анализ диалога", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self.analysis_panel
                ]),
                expand=True,
                padding=20,
                border_radius=10,
                bgcolor=ft.Colors.GREY_900,
                margin=ft.margin.only(left=10)
            )
        ], expand=True)

        # Собираем все вместе
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Text("🤖 X - AI Telegram Assistant",
                                       size=24, weight=ft.FontWeight.BOLD,
                                       color=primary_color),
                        padding=ft.padding.all(20)
                    ),
                    ft.Container(
                        content=status_row,
                        padding=ft.padding.symmetric(horizontal=20),
                        border_radius=10,
                        bgcolor=ft.Colors.GREY_900,
                        margin=ft.margin.only(bottom=10)
                    ),
                    ft.Container(
                        content=controls_row,
                        padding=ft.padding.symmetric(horizontal=20, vertical=10)
                    ),
                    main_content
                ]),
                expand=True
            )
        )

        # Контейнер для уведомлений (в правом верхнем углу)
        self.notification_container = ft.Container(
            content=ft.Column([]),
            alignment=ft.alignment.top_right,
            width=300,
            height=100
        )

        # Добавляем контейнер уведомлений в overlay
        page.overlay.append(self.notification_container)

        # Инициализация AI клиента
        self.ai_client = Mistral(api_key=MISTRAL_API_KEY)

    def show_notification(self, message, color):
        """Показать уведомление в правом верхнем углу"""
        try:
            print(f"📢 Показываем уведомление: {message}")

            # Создаем уведомление
            notification = ft.Container(
                content=ft.Text(message, color=ft.Colors.WHITE, size=14, weight=ft.FontWeight.BOLD),
                bgcolor=color,
                padding=ft.padding.all(15),
                border_radius=10,
                margin=ft.margin.only(bottom=10),
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=ft.Colors.BLACK38,
                    offset=ft.Offset(0, 2)
                )
            )

            # Добавляем уведомление
            if self.notification_container and self.notification_container.content:
                self.notification_container.content.controls.append(notification)
                self.page.update()

                # Автоматически убираем через 3 секунды
                async def remove_notification():
                    try:
                        await asyncio.sleep(3)
                        if (notification in self.notification_container.content.controls):
                            self.notification_container.content.controls.remove(notification)
                            self.page.update()
                    except Exception as e:
                        print(f"❌ Ошибка удаления уведомления: {e}")

                # Запускаем удаление в фоне
                asyncio.create_task(remove_notification())

        except Exception as e:
            print(f"❌ Ошибка показа уведомления: {e}")

    async def on_auto_response_sent(self, dialog_entity, response, sender_name):
        """Callback для обновления UI после автоматической отправки ответа"""
        try:
            print(f"🔄 UI Callback: Авто-ответ отправлен для {sender_name}")

            # Обновляем счетчики
            self.stats["responses_sent"] += 1
            self.stats["processed"] += 1
            self.stats_responses.value = str(self.stats["responses_sent"])
            self.stats_processed.value = str(self.stats["processed"])

            # Обновляем список диалогов (убираем синий кружок)
            await self.load_dialogs()

            # Показываем уведомление
            self.show_notification(
                f"🤖 Авто-ответ отправлен: {sender_name}",
                ft.Colors.BLUE_600
            )

            print(f"📊 UI обновлен: Отправлено={self.stats['responses_sent']}, Обработано={self.stats['processed']}")

        except Exception as e:
            print(f"❌ Ошибка в UI callback: {e}")

    async def start_message_listener(self):
        """Запуск мониторинга новых сообщений для обновления UI"""
        if not self.telegram_reader or self.message_listener_active:
            return

        print("🔄 Запускаем мониторинг новых сообщений для UI...")
        self.message_listener_active = True

        # Устанавливаем обработчик новых сообщений
        from telethon import events

        @self.telegram_reader.client.on(events.NewMessage(incoming=True))
        async def handle_new_message_ui(event):
            try:
                # Проверяем, что это личное сообщение
                if not event.is_private:
                    return

                sender = await event.get_sender()
                dialog_entity = await event.get_chat()

                print(f"\n📨 UI: Новое сообщение от {getattr(sender, 'first_name', 'Unknown')} ({sender.id})")
                print(f"📝 Текст: {event.message.text}")

                # Проверяем, является ли этот диалог лидом
                is_lead = await self.telegram_reader.is_lead_dialog(dialog_entity)
                print(f"🎯 UI: Диалог является лидом: {is_lead}")

                if is_lead:
                    print("🔄 UI: Обновляем список диалогов...")

                    # Обновляем список диалогов
                    await self.load_dialogs()

                    # Показываем уведомление о новом сообщении
                    sender_name = getattr(sender, 'first_name', 'Неизвестно')
                    if hasattr(sender, 'last_name') and sender.last_name:
                        sender_name += f" {sender.last_name}"

                    message_preview = event.message.text[:30] + ("..." if len(event.message.text) > 30 else "")

                    self.show_notification(
                        f"💬 Новое сообщение от {sender_name}: {message_preview}",
                        ft.Colors.BLUE_600
                    )

                    print("✅ UI: Список диалогов обновлен")

            except Exception as e:
                print(f"❌ UI: Ошибка обработки нового сообщения: {e}")

    async def connect_to_telegram(self):
        """Подключение к Telegram"""
        try:
            self.connection_status.value = "🔄 Подключение..."
            self.connection_status.color = ft.Colors.ORANGE_600
            self.page.update()

            # Создаем TelegramReader в отдельном потоке
            await asyncio.sleep(0.1)  # Небольшая задержка для UI

            self.telegram_reader = TelegramReader(TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE)
            await self.telegram_reader.connect()

            self.connection_status.value = "✅ Подключен"
            self.connection_status.color = ft.Colors.GREEN_600
            self.page.update()

            # Загружаем диалоги
            await self.load_dialogs()

            # Запускаем мониторинг новых сообщений
            await self.start_message_listener()

        except Exception as e:
            self.connection_status.value = f"❌ Ошибка: {str(e)[:30]}..."
            self.connection_status.color = ft.Colors.RED_600
            self.page.update()

    async def load_dialogs(self):
        """Загрузка списка диалогов"""
        if not self.telegram_reader:
            print("❌ TelegramReader не инициализирован")
            return

        try:
            print("🔄 Загружаем диалоги...")

            # Используем метод для получения только лидов
            leads = await self.telegram_reader.get_leads_only()
            print(f"📊 Найдено лидов: {len(leads)}")

            if len(leads) == 0:
                print("⚠️ Лидов не найдено. Попробуем загрузить все диалоги...")
                # Если лидов нет, покажем все диалоги для отладки
                all_dialogs = await self.telegram_reader.get_all_dialogs()
                print(f"📋 Всего диалогов: {len(all_dialogs)}")

                # Показываем первые 3 диалога для отладки
                for i, dialog in enumerate(all_dialogs[:3]):
                    print(f"  {i+1}. {dialog['name']} (ID: {dialog['id']}, Тип: {'Пользователь' if dialog['is_user'] else 'Группа/Канал'})")

            # Сортируем диалоги: сначала те, которые требуют ответа, потом по времени
            sorted_leads = []
            for lead_data in leads:
                dialog = lead_data['dialog']
                messages = lead_data['messages']

                # Проверяем, нужен ли ответ
                needs_response = await self.telegram_reader.dialog_needs_response(dialog['entity'])

                # Получаем время последнего сообщения
                last_message_time = None
                if messages:
                    last_msg = messages[-1]
                    last_message_time = last_msg.get('date')

                # Добавляем метаданные
                lead_data['needs_response'] = needs_response
                lead_data['last_message_time'] = last_message_time
                sorted_leads.append(lead_data)

            # Сортируем: сначала непрочитанные, потом по времени (новые сверху)
            sorted_leads.sort(key=lambda x: (
                not x['needs_response'],  # False идет первым (непрочитанные сверху)
                -(x['last_message_time'].timestamp() if x['last_message_time'] else 0)  # Новые сверху
            ))

            self.dialogs = sorted_leads
            self.stats["leads"] = len(sorted_leads)
            self.stats_leads.value = str(len(sorted_leads))
            self.page.update()

            # Обновляем UI список
            await self.update_dialogs_ui()
            print("✅ Список диалогов обновлен")

        except Exception as e:
            print(f"❌ Ошибка загрузки диалогов: {e}")
            import traceback
            traceback.print_exc()

    async def update_dialogs_ui(self):
        """Обновление UI списка диалогов"""
        print(f"🎨 Обновляем UI для {len(self.dialogs)} диалогов...")
        self.dialogs_list.controls.clear()

        if len(self.dialogs) == 0:
            # Показываем сообщение о том, что диалогов нет
            no_dialogs_msg = ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.CHAT_BUBBLE_OUTLINE, size=48, color=ft.Colors.GREY_400),
                    ft.Text("Лиды не найдены", size=16, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER),
                    ft.Text("Диалоги с испанскими сообщениями появятся здесь", size=12, color=ft.Colors.GREY_500, text_align=ft.TextAlign.CENTER)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                padding=30,
                alignment=ft.alignment.center
            )
            self.dialogs_list.controls.append(no_dialogs_msg)
            self.page.update()
            return

        for i, lead_data in enumerate(self.dialogs):
            print(f"  🔄 Обрабатываем диалог {i+1}/{len(self.dialogs)}")
            dialog = lead_data['dialog']
            messages = lead_data['messages']

            # Получаем информацию о диалоге
            dialog_name = getattr(dialog['entity'], 'first_name', '') or getattr(dialog['entity'], 'title', 'Неизвестно')
            if hasattr(dialog['entity'], 'last_name') and dialog['entity'].last_name:
                dialog_name += f" {dialog['entity'].last_name}"

            # Последнее сообщение
            last_message = "Нет сообщений"
            if messages:
                last_msg = messages[-1]  # Последнее сообщение
                last_message = last_msg['text'][:50] + ("..." if len(last_msg['text']) > 50 else "")

            # Получаем статус из предзагруженных данных
            needs_response = lead_data.get('needs_response', False)

            # Время последнего сообщения
            time_text = "Давно"
            if messages:
                last_msg = messages[-1]
                if last_msg['date']:
                    time_diff = datetime.now() - last_msg['date'].replace(tzinfo=None)
                    if time_diff.days > 0:
                        time_text = f"{time_diff.days} дн. назад"
                    elif time_diff.seconds > 3600:
                        time_text = f"{time_diff.seconds // 3600} ч. назад"
                    else:
                        time_text = f"{time_diff.seconds // 60} мин. назад"

            # Обработчик клика - отмечает диалог как прочитанный
            async def dialog_clicked(e, d=lead_data):
                print(f"🖱️ Клик по диалогу: {dialog_name}")

                # Отмечаем диалог как прочитанный в Telegram
                if d.get('needs_response', False):
                    print("📖 Отмечаем диалог как прочитанный в Telegram...")
                    dialog_entity = d['dialog']['entity']
                    success = await self.telegram_reader.mark_dialog_as_read(dialog_entity)

                    if success:
                        print("✅ Статус 'прочитано' отправлен в Telegram")
                        # Показываем уведомление об успехе
                        self.show_notification(f"📖 Диалог с {dialog_name} отмечен как прочитанный", ft.Colors.GREEN_600)
                    else:
                        print("❌ Не удалось отправить статус 'прочитано' в Telegram")
                        self.show_notification(f"❌ Ошибка отметки диалога как прочитанного", ft.Colors.RED_600)

                # Отмечаем диалог как прочитанный в UI (убираем синий кружок)
                d['needs_response'] = False

                self.selected_dialog = d
                await self.analyze_dialog(d)

                # Перестраиваем UI чтобы убрать синий кружок
                await self.update_dialogs_ui()

            # Создаем элементы строки диалога
            name_text = ft.Text(
                f"🇪🇸 {dialog_name}",
                weight=ft.FontWeight.BOLD if needs_response else ft.FontWeight.NORMAL,
                expand=True,
                color=ft.Colors.WHITE if needs_response else ft.Colors.GREY_300
            )

            # Синий кружочек только для непрочитанных (как в Telegram)
            status_indicator = None
            if needs_response:
                status_indicator = ft.Container(
                    content=ft.Text("●", size=8, color=ft.Colors.WHITE),
                    width=16,
                    height=16,
                    bgcolor=ft.Colors.BLUE_600,
                    border_radius=8,
                    alignment=ft.alignment.center,
                    tooltip="Непрочитанные сообщения"
                )

            time_element = ft.Text(time_text, size=12, color=ft.Colors.GREY_400)

            # Последнее сообщение
            message_text = ft.Text(
                last_message,
                size=12,
                color=ft.Colors.GREY_300 if not needs_response else ft.Colors.GREY_200,
                max_lines=2,
                weight=ft.FontWeight.NORMAL
            )

            # Создаем строку с элементами
            top_row_elements = [name_text]
            if status_indicator:
                top_row_elements.append(status_indicator)
            top_row_elements.append(time_element)

            dialog_card = ft.Container(
                content=ft.Column([
                    ft.Row(top_row_elements),
                    message_text
                ]),
                padding=15,
                border_radius=8,
                bgcolor=ft.Colors.GREY_800,  # Одинаковый фон для всех
                border=ft.border.all(1, ft.Colors.GREY_700),
                on_click=dialog_clicked,
                ink=True,
                animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT)
            )

            self.dialogs_list.controls.append(dialog_card)

        self.page.update()

    async def analyze_dialog(self, lead_data):
        """Анализ выбранного диалога"""
        try:
            # Показываем процесс анализа
            self.analysis_panel.content = ft.Column([
                ft.Text("🔄 Анализируется диалог...", size=16),
                ft.ProgressRing()
            ])
            self.page.update()

            # Используем уже готовый форматированный контекст
            lead_dialogue = lead_data['formatted_context']
            dialog = lead_data['dialog']

            # Используем системный промпт из конфигурации

            # Получаем анализ от AI
            chat_response = self.ai_client.chat.complete(
                model=MISTRAL_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": lead_dialogue
                    }
                ]
            )

            analysis = chat_response.choices[0].message.content

            # Отладочный вывод
            print(f"📊 Полный анализ от AI:\n{analysis}\n" + "="*50)

            # Извлекаем компоненты анализа
            lines = analysis.split('\n')
            phase = "Неопределено"
            dialog_type = "Неопределено"
            context = "Нет контекста"
            response = "Нет ответа"

            for line in lines:
                if 'Фаза:' in line:
                    phase = line.split('Фаза:', 1)[1].strip().replace('**', '')
                elif 'Тип:' in line:
                    dialog_type = line.split('Тип:', 1)[1].strip().replace('**', '')
                elif 'Контекст:' in line:
                    context = line.split('Контекст:', 1)[1].strip().replace('**', '')

            # Используем более надёжную функцию для извлечения ответа
            extracted_response = extract_response_from_analysis(analysis)
            if extracted_response:
                response = extracted_response
                print(f"✅ Извлечен ответ функцией: {response}")
            else:
                # Fallback к простому методу
                for line in lines:
                    if 'Ответ:' in line:
                        response = line.split('Ответ:', 1)[1].strip().replace('**', '')
                        print(f"⚠️ Fallback извлечение: {response}")
                        break

            print(f"🎯 Финальный ответ для UI: '{response}'")

            # Создаем контейнер для ответа отдельно, чтобы можно было его обновлять
            response_container = ft.Container(
                content=ft.Text(response, size=14),
                padding=10,
                border_radius=5,
                bgcolor=ft.Colors.GREY_800
            )

            # Кнопки действий
            async def send_response(e):
                # Визуальный эффект - кнопка становится неактивной
                send_btn = e.control
                send_btn.disabled = True
                send_btn.text = "📤 Отправляется..."
                send_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREY_600)
                self.page.update()

                try:
                    await self.send_response_to_dialog(dialog, response)

                    # Успешная отправка - зеленая кнопка
                    send_btn.text = "✅ Отправлено!"
                    send_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_700)
                    self.page.update()

                    # Показываем уведомление
                    self.show_notification("✅ Сообщение успешно отправлено лиду!", ft.Colors.GREEN_600)

                except Exception as ex:
                    # Ошибка отправки - красная кнопка
                    send_btn.text = "❌ Ошибка"
                    send_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.RED_600)
                    self.page.update()

                    # Показываем уведомление об ошибке
                    self.show_notification(f"❌ Ошибка отправки: {str(ex)}", ft.Colors.RED_600)

                # Через 2 секунды возвращаем кнопку в исходное состояние
                await asyncio.sleep(2)
                send_btn.disabled = False
                send_btn.text = "📤 Отправить"
                send_btn.style = ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)
                self.page.update()

            def edit_response(e):
                print("🔧 Кнопка 'Изменить' нажата!")  # Отладка
                print(f"📝 Текущий ответ для редактирования: '{response}'")

                # Попробуем BottomSheet вместо AlertDialog
                def close_bs(e):
                    bs.open = False
                    self.page.update()

                def save_text(e):
                    nonlocal response
                    new_text = txt_field.value
                    print(f"💾 Новый текст: '{new_text}'")
                    response = new_text
                    response_container.content = ft.Text(response, size=14)
                    bs.open = False
                    self.page.update()

                txt_field = ft.TextField(
                    label="Редактировать ответ",
                    value=response,
                    multiline=True,
                    min_lines=5,
                    max_lines=10,
                    width=500
                )

                bs = ft.BottomSheet(
                    ft.Container(
                        ft.Column([
                            ft.Text("✏️ Редактировать ответ", size=20, weight=ft.FontWeight.BOLD),
                            ft.Divider(),
                            txt_field,
                            ft.Row([
                                ft.TextButton("❌ Отмена", on_click=close_bs),
                                ft.TextButton("💾 Сохранить", on_click=save_text)
                            ], alignment=ft.MainAxisAlignment.END)
                        ], scroll=ft.ScrollMode.AUTO),
                        padding=20,
                        width=600,
                        height=400
                    ),
                    open=True
                )

                self.page.overlay.append(bs)
                self.page.update()
                print("✅ BottomSheet создан и добавлен")

            async def skip_dialog(e):
                # Обновляем счетчик обработанных (пропуск тоже считается обработкой)
                self.stats["processed"] += 1
                self.stats_processed.value = str(self.stats["processed"])
                print(f"📊 Диалог пропущен! Всего обработано: {self.stats['processed']}")

                # Показываем уведомление о пропуске
                self.analysis_panel.content.controls.append(
                    ft.Container(
                        content=ft.Text("⏭️ Диалог пропущен", color=ft.Colors.ORANGE_400),
                        padding=10,
                        border_radius=5,
                        bgcolor=ft.Colors.ORANGE_100
                    )
                )
                self.page.update()

            # Обновляем панель анализа
            self.analysis_panel.content = ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Text("📊 Результат анализа", size=16, weight=ft.FontWeight.BOLD),
                        ft.Divider(),
                        ft.Row([
                            ft.Text("Фаза:", weight=ft.FontWeight.BOLD),
                            ft.Text(phase, color=ft.Colors.BLUE_400)
                        ]),
                        ft.Row([
                            ft.Text("Тип:", weight=ft.FontWeight.BOLD),
                            ft.Text(dialog_type, color=ft.Colors.GREEN_400)
                        ]),
                        ft.Text("Контекст:", weight=ft.FontWeight.BOLD),
                        ft.Container(
                            content=ft.Text(context, size=12),
                            padding=10,
                            border_radius=5,
                            bgcolor=ft.Colors.GREY_800
                        )
                    ])
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("💬 Рекомендуемый ответ", size=16, weight=ft.FontWeight.BOLD),
                        response_container,
                        ft.Row([
                            ft.ElevatedButton(
                                "📤 Отправить",
                                on_click=send_response,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600)
                            ),
                            ft.ElevatedButton(
                                "✏️ Изменить",
                                on_click=lambda e: print("КНОПКА ИЗМЕНИТЬ НАЖАТА!") or edit_response(e),
                                style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600)
                            ),
                            ft.ElevatedButton(
                                "⏭️ Пропустить",
                                on_click=skip_dialog,
                                style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_600)
                            )
                        ], spacing=10)
                    ])
                )
            ], scroll=ft.ScrollMode.AUTO)

            self.page.update()

        except Exception as e:
            self.analysis_panel.content = ft.Column([
                ft.Text(f"❌ Ошибка анализа: {str(e)}", color=ft.Colors.RED_400)
            ])
            self.page.update()

    async def send_response_to_dialog(self, dialog, response):
        """Отправка ответа в диалог"""
        try:
            # Используем entity из dialog для отправки
            dialog_entity = dialog['entity']
            success = await self.telegram_reader.send_message(dialog_entity, response)

            if success:
                self.stats["responses_sent"] += 1
                self.stats["processed"] += 1
                self.stats_responses.value = str(self.stats["responses_sent"])
                self.stats_processed.value = str(self.stats["processed"])
                self.page.update()
                print(f"📊 Сообщение отправлено! Отправлено: {self.stats['responses_sent']}, Обработано: {self.stats['processed']}")

                # Показываем уведомление об успехе
                self.analysis_panel.content.controls.append(
                    ft.Container(
                        content=ft.Text("✅ Ответ отправлен!", color=ft.Colors.GREEN_400),
                        padding=10,
                        border_radius=5,
                        bgcolor=ft.Colors.GREEN_100
                    )
                )
            else:
                self.analysis_panel.content.controls.append(
                    ft.Container(
                        content=ft.Text("❌ Ошибка отправки сообщения", color=ft.Colors.RED_400),
                        padding=10,
                        border_radius=5,
                        bgcolor=ft.Colors.RED_100
                    )
                )

            self.page.update()

        except Exception as e:
            self.analysis_panel.content.controls.append(
                ft.Container(
                    content=ft.Text(f"❌ Ошибка отправки: {str(e)}", color=ft.Colors.RED_400),
                    padding=10,
                    border_radius=5,
                    bgcolor=ft.Colors.RED_100
                )
            )
            self.page.update()

    async def toggle_auto_responder(self):
        """Переключение авто-ответчика"""
        if not self.telegram_reader:
            return

        if not self.auto_responder_active:
            self.auto_responder_active = True
            self.auto_responder_status.value = "▶️ Активен"
            self.auto_responder_status.color = ft.Colors.GREEN_600
            self.page.update()

            # Запускаем мониторинг в фоне
            asyncio.create_task(self.run_auto_responder())
        else:
            self.auto_responder_active = False
            self.auto_responder_status.value = "⏸️ Остановлен"
            self.auto_responder_status.color = ft.Colors.ORANGE_600
            self.page.update()

    async def run_auto_responder(self):
        """Запуск авто-ответчика"""
        try:
            # Используем системный промпт для авто-ответчика из конфигурации

            # Настраиваем авто-ответчик с callback для обновления UI
            await self.telegram_reader.setup_auto_responder(
                self.ai_client,
                SYSTEM_PROMPT,
                MISTRAL_MODEL,
                ui_callback=self.on_auto_response_sent
            )

            # Сначала обрабатываем существующие непрочитанные сообщения
            await self.telegram_reader.process_existing_unread_leads()

            # Затем запускаем мониторинг новых сообщений
            await self.telegram_reader.start_monitoring()

        except Exception as e:
            self.auto_responder_status.value = f"❌ Ошибка: {str(e)[:20]}..."
            self.auto_responder_status.color = ft.Colors.RED_600
            self.page.update()

def run_app():
    """Запуск приложения"""
    app = SantiagoUI()
    ft.app(target=app.main, view=ft.AppView.FLET_APP)

if __name__ == "__main__":
    run_app()