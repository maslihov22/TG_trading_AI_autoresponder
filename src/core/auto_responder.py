"""
Автоматический ответчик для лидов в Telegram
Работает в режиме реального времени, отвечает только на испанские сообщения
"""

import asyncio
import os
from mistralai import Mistral

# Импорты из config (first-party)
from config.settings import (
    MISTRAL_API_KEY,
    MISTRAL_MODEL,
    SYSTEM_PROMPT,
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_PHONE
)

# Локальные импорты
from .telegram_client import TelegramReader, extract_response_from_analysis
from .kb_retriever import KBRetriever

class AutoResponder:
    def __init__(self):
        """Инициализация автоответчика"""
        self.ai_client = Mistral(api_key=MISTRAL_API_KEY)
        self.telegram = TelegramReader(TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE)
        self.is_running = False
        self.kb_retriever = None

    async def start(self):
        """Запустить систему автоответчика"""
        try:
            print("🚀 Запуск Auto-Responder с RAG")
            print("=" * 50)

            # Инициализация KB Retriever
            print("📚 Инициализация Knowledge Base Retriever...")
            kb_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'kb')
            self.kb_retriever = KBRetriever(kb_dir, self.ai_client)

            # Построение индекса
            print("🔨 Построение FAISS индекса из KB...")
            self.kb_retriever.build_index()
            print("✅ Индекс готов")

            # Подключиться к Telegram
            await self.telegram.connect()
            print("✅ Подключен к Telegram")

            # Настроить автоответчик с RAG
            await self.telegram.setup_auto_responder(
                ai_client=self.ai_client,
                system_prompt=SYSTEM_PROMPT,
                model=MISTRAL_MODEL,
                kb_retriever=self.kb_retriever  # Передаём retriever
            )
            print("✅ Автоответчик настроен с RAG")

            # Отметить как функционирующий
            self.is_running = True
            print("✅ Система готова")
            print("\n" + "=" * 50)

            # Запустить мониторинг
            await self.telegram.start_monitoring()

        except KeyboardInterrupt:
            print("\n\n🛑 Остановка Auto-Responder...")
            await self.stop()
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            await self.stop()

    async def stop(self):
        """Остановить систему"""
        if self.is_running:
            self.is_running = False
            await self.telegram.close()
            print("✅ Автоответчик остановлен")

    async def test_lead_detection(self):
        """Проверить детекцию лидов"""
        print("🧪 Проверить детекцию лидов...")

        leads = await self.telegram.get_leads_only()
        print(f"🎯 Найдено {len(leads)} лидов")

        for lead in leads:
            dialog = lead['dialog']
            print(f"📊 Лид: {dialog['name']} (ID: {dialog['id']})")
            print(f"   Последний контекст: {lead['formatted_context'][:100]}...")
            print("-" * 40)

    async def test_unread_detection(self):
        """Проверить детекцию сообщений без ответа"""
        print("🧪 Проверить детекцию сообщений без ответа...")

        unread_leads = await self.telegram.get_unread_leads()
        print(f"📬 {len(unread_leads)} лидов нуждаются в ответе")

        for lead in unread_leads:
            dialog = lead['dialog']
            print(f"⏰ Ответить на: {dialog['name']} (ID: {dialog['id']})")

