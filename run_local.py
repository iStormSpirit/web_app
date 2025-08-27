import threading
import time
from local_bot import start_bot
from local_api import run_api_server
from local_web_server import run_web_server


def main():
    print("🚀 ЗАПУСК ЛОКАЛЬНОЙ СИСТЕМЫ")
    print("=" * 50)

    # Запускаем API сервер в отдельном потоке
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()

    # Запускаем веб-сервер в отдельном потоке
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Даем серверам время на запуск
    time.sleep(2)

    print("✅ Серверы запущены")
    print("🌐 Web Server: http://localhost:8080")
    print("🔌 API Server: http://localhost:8000")
    print("🤖 Запускаем бота...")
    print("=" * 50)

    # Запускаем бота в основном потоке
    try:
        start_bot()
    except KeyboardInterrupt:
        print("\n🛑 Остановка системы...")


if __name__ == "__main__":
    main()