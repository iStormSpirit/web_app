from http.server import HTTPServer, SimpleHTTPRequestHandler
import os


class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):

    def end_headers(self):
        # Добавляем CORS headers для работы с Telegram
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


def run_web_server():
    """Запуск локального веб-сервера"""
    # Создаем директорию для webapp если ее нет
    if not os.path.exists('webapp'):
        os.makedirs('webapp')

    # Меняем рабочую директорию на webapp
    os.chdir('webapp')

    server_address = ('localhost', 8080)
    httpd = HTTPServer(server_address, CORSHTTPRequestHandler)
    print(f"🌐 Локальный веб-сервер запущен на http://localhost:8080")
    print("📁 Обслуживаем файлы из папки 'webapp'")
    httpd.serve_forever()