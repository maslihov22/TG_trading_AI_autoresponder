"""
Config модуль - конфигурация приложения
"""

from .settings import *

__all__ = [
    'MISTRAL_API_KEY', 'MISTRAL_MODEL',
    'TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE',
    'DEFAULT_MESSAGE_LIMIT', 'SYSTEM_PROMPT'
]