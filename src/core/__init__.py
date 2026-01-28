"""
Core модуль - основная логика приложения
"""

from .telegram_client import TelegramReader
from .auto_responder import AutoResponder

__all__ = ['TelegramReader', 'AutoResponder']