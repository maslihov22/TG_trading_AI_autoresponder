"""
X Telegram Bot - Главная точка входа
Запуск GUI приложения для автоматических ответов в Telegram
"""

import sys
import os

# Добавляем путь к src для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app import run_app
def main():
    """Главная функция запуска приложения"""
    print("Запуск Telegram Bot...")
    run_app()

if __name__ == "__main__":
    main()