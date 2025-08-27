from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from urllib.parse import urlparse, parse_qs, unquote
import pprint

from anyio import typed_attribute


def parse_init_data(init_data_string):
    """
    Парсит initData строку из Telegram в JSON объект
    """
    try:
        # Декодируем URL-encoded строку
        decoded = unquote(init_data_string)

        # Парсим query string
        parsed_data = parse_qs(decoded)

        # Преобразуем списки в одиночные значения
        result = {}
        for key, value in parsed_data.items():
            # Берем первый элемент если это список
            if isinstance(value, list) and len(value) == 1:
                result[key] = value[0]
            else:
                result[key] = value

        # Пытаемся распарсить JSON поля (user, receiver, chat)
        json_fields = ['user', 'receiver', 'chat']
        for field in json_fields:
            if field in result:
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, TypeError):
                    # Если не JSON, оставляем как есть
                    pass

        return result

    except Exception as e:
        # Возвращаем ошибку с оригинальной строкой
        return {
            "error": str(e),
            "raw_string": init_data_string,
            "decoded_string": decoded if 'decoded' in locals() else None
        }

class LocalAPIHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        """Обработка POST запросов"""
        if self.path == '/api':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                self.handle_api_data(data)
            except json.JSONDecodeError as e:
                print(f"❌ Ошибка парсинга JSON: {e}")
                print(f"📦 Raw data: {post_data.decode('utf-8')}")
                self.send_error(400, "Invalid JSON")

        else:
            self.send_error(404, "Not Found")

    def handle_api_data(self, data):
        """Обработка данных от бота"""
        print("\n" + "=" * 80)
        print("🚀 ПОЛУЧЕНЫ ДАННЫЕ ОТ БОТА:")
        print("=" * 80)

        action = data.get('action', 'unknown')
        print(f"📋 Action: {action}")

        # Красиво выводим ВСЕ данные
        print("\n📊 ПОЛНЫЕ ДАННЫЕ:")
        print("-" * 40)

        # Используем pprint для красивого вывода
        pp = pprint.PrettyPrinter(indent=2, width=100)

        # sup_data = parse_init_data(data)
        print(type(data))
        print(data)
        # pp.pprint(data)

        print("-" * 40)

        # Детальный вывод в зависимости от действия
        if action == 'start_command':
            print(f"\n👤 User: {data.get('first_name')} (@{data.get('username')})")
            print(f"🆔 User ID: {data.get('user_id')}")
            print(f"💬 Chat ID: {data.get('chat_id')}")

        elif action == 'message':
            print(f"\n👤 User: {data.get('first_name')} (@{data.get('username')})")
            print(f"💬 Message: {data.get('text')}")
            print(f"📅 Date: {data.get('date')}")

        elif action == 'auth_simulation':
            print("\n🎯 IMITATED AUTH DATA:")
            init_data = data.get('init_data', {})
            if 'simulated_data' in init_data:
                sim_data = init_data['simulated_data']
                print(f"👤 User: {sim_data.get('user', {}).get('first_name', 'N/A')}")
                print(f"🆔 User ID: {sim_data.get('user', {}).get('id', 'N/A')}")
                print(f"🔐 Hash: {sim_data.get('hash', 'N/A')}")

            # Выводим полную initData структуру
            print("\n📋 FULL INITDATA STRUCTURE:")
            print("-" * 30)
            if 'init_data' in data:
                pp.pprint(data['init_data'])

        elif action == 'webapp_auth':
            print("\n🎯 WEB APP AUTHORIZATION DATA:")
            init_data = data.get('init_data', {})

            # Выводим сырые данные
            if 'raw_data' in init_data:
                print(f"📦 Raw initData: {init_data['raw_data']}")

            # Выводим распарсенные данные
            if 'parsed_data' in init_data:
                print("\n🔍 PARSED INITDATA:")
                print("-" * 25)
                pp.pprint(init_data['parsed_data'])

            # Выводим пользовательские данные
            if 'parsed_data' in init_data and 'user' in init_data['parsed_data']:
                user_data = init_data['parsed_data']['user']
                if isinstance(user_data, dict):
                    print(f"\n👤 User: {user_data.get('first_name', '')} {user_data.get('last_name', '')}")
                    print(f"📧 Username: @{user_data.get('username', 'N/A')}")
                    print(f"🆔 User ID: {user_data.get('id', 'N/A')}")

        print("\n" + "=" * 80)

        # Отправляем успешный ответ
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "success", "received": True}
        self.write_json(response)

    def do_GET(self):
        """Обработка GET запросов (для проверки работы)"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <h1>Local API Server is Running!</h1>
                <p>API endpoint: <code>/api</code></p>
                <p>Check console for incoming data from bot</p>
            """)
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.write_json({"status": "running", "port": 8000})
        else:
            self.send_error(404, "Not Found")

    def write_json(self, data):
        """Вспомогательная функция для отправки JSON"""
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def log_message(self, format, *args):
        """Кастомное логирование"""
        print(f"🌐 API Request: {self.address_string()} - {format % args}")

    def log_request(self, code='-', size='-'):
        """Переопределяем логирование запросов"""
        if self.path != '/':
            print(f"📡 {self.command} {self.path} - {code}")


def run_api_server():
    """Запуск локального API сервера"""
    server_address = ('localhost', 8000)
    httpd = HTTPServer(server_address, LocalAPIHandler)

    print(f"🚀 Локальный API сервер запущен на http://localhost:8000")
    print(f"📡 API endpoint: http://localhost:8000/api")
    print(f"🔍 Status check: http://localhost:8000/status")
    print("=" * 60)
    print("Ожидаем данные от бота...")
    print("=" * 60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Остановка API сервера...")
    except Exception as e:
        print(f"❌ Ошибка сервера: {e}")


if __name__ == "__main__":
    run_api_server()