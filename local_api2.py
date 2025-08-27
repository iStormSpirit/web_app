from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs


class LocalAPIHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        """Обработка POST запросов"""
        if self.path == '/api':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                self.handle_api_data(data)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")

        else:
            self.send_error(404, "Not Found")

    def handle_api_data(self, data):
        """Обработка данных от бота"""
        print("\n" + "=" * 60)
        print("🚀 ПОЛУЧЕНЫ ДАННЫЕ ОТ БОТА:")
        print("=" * 60)

        action = data.get('action', 'unknown')
        print(f"📋 Action: {action}")

        if action == 'start_command':
            print(f"👤 User: {data.get('first_name')} (@{data.get('username')})")
            print(f"🆔 User ID: {data.get('user_id')}")
            print(f"💬 Chat ID: {data.get('chat_id')}")

        elif action == 'message':
            print(f"👤 User: {data.get('first_name')} (@{data.get('username')})")
            print(f"💬 Message: {data.get('text')}")
            print(f"📅 Date: {data.get('date')}")

        elif action == 'webapp_auth':
            print("🎯 WEB APP AUTHORIZATION DATA:")
            init_data = data.get('init_data', {})
            if 'user' in init_data:
                user = init_data['user']
                if isinstance(user, dict):
                    print(f"👤 User: {user.get('first_name')} {user.get('last_name', '')}")
                    print(f"📧 Username: @{user.get('username', 'N/A')}")
                    print(f"🆔 User ID: {user.get('id')}")
            print(f"📊 Raw initData: {data.get('raw_data')}")

        print("=" * 60)

        # Отправляем успешный ответ
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "success", "received": True}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        """Обработка GET запросов (для проверки работы)"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Local API Server is Running!</h1>")
        else:
            self.send_error(404, "Not Found")

    def log_message(self, format, *args):
        """Кастомное логирование"""
        print(f"🌐 API Request: {self.address_string()} - {format % args}")


def run_api_server():
    """Запуск локального API сервера"""
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, LocalAPIHandler)
    print(f"🚀 Локальный API сервер запущен на http://localhost:8000")
    print("📡 Ожидаем данные от бота...")
    httpd.serve_forever()