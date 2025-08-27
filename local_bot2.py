import logging
import requests
from telegram import Update, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация для локальной работы
BOT_TOKEN = "8222846517:AAEVXzNlrt14BWIK2QrA38JE72doZ2Fy3YE"  # Замените на токен вашего бота
LOCAL_API_URL = "http://localhost:8000/api"  # Локальный API
LOCAL_WEBAPP_URL = "http://localhost:8080/webapp.html"  # Локальный веб-сервер


# Клавиатура с кнопкой авторизации
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🔐 Авторизоваться", web_app=WebAppInfo(url=LOCAL_WEBAPP_URL))]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 Добро пожаловать!\n\n"
        "Нажмите кнопку 'Авторизоваться' для входа через Telegram Web App.\n"
        "Все ваши действия будут отправлены на локальный сервер."
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

    # Отправляем данные на локальный API
    user_data = {
        "action": "start_command",
        "user_id": update.effective_user.id,
        "username": update.effective_user.username,
        "first_name": update.effective_user.first_name,
        "last_name": update.effective_user.last_name,
        "chat_id": update.effective_chat.id
    }

    await send_to_local_api(user_data)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений"""
    user = update.effective_user
    message = update.message

    # Выводим в консоль бота
    print("📨 Получено сообщение:")
    print(f"👤 User: {user.first_name} (@{user.username})")
    print(f"🆔 ID: {user.id}")
    print(f"💬 Text: {message.text}")
    print(f"📋 Chat ID: {message.chat_id}")
    print("-" * 40)

    # Формируем данные для отправки на API
    message_data = {
        "action": "message",
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "chat_id": message.chat_id,
        "message_id": message.message_id,
        "text": message.text,
        "date": message.date.isoformat()
    }

    # Отправляем на локальный API
    await send_to_local_api(message_data)

    # Отправляем подтверждение пользователю
    await message.reply_text(
        "✅ Ваше сообщение получено и отправлено на локальный сервер!",
        reply_markup=get_main_keyboard()
    )


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик данных из Web App"""
    web_app_data = update.effective_message.web_app_data

    print("🎯 Получены данные из Web App:")
    print(f"Data: {web_app_data.data}")
    print("-" * 40)

    # Парсим initData
    try:
        init_data = parse_init_data(web_app_data.data)

        webapp_data = {
            "action": "webapp_auth",
            "init_data": init_data,
            "raw_data": web_app_data.data,
            "user_id": update.effective_user.id,
            "chat_id": update.effective_chat.id
        }

        # Отправляем на локальный API
        await send_to_local_api(webapp_data)

        await update.message.reply_text(
            "✅ Авторизация успешна! Данные отправлены на локальный сервер.",
            reply_markup=get_main_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка обработки WebApp data: {e}")
        await update.message.reply_text("❌ Ошибка обработки данных авторизации.")


def parse_init_data(raw_data: str) -> dict:
    """Парсит initData из query string в словарь"""
    result = {}
    try:
        # Декодируем URL-encoded строку
        decoded_data = urllib.parse.unquote(raw_data)
        for pair in decoded_data.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                result[key] = value

        # Если есть user данные, пробуем распарсить JSON
        if 'user' in result:
            try:
                result['user'] = json.loads(result['user'])
            except:
                pass
    except Exception as e:
        logger.error(f"Ошибка парсинга initData: {e}")
        result = {"raw": raw_data, "error": str(e)}

    return result


async def send_to_local_api(data: dict):
    """Отправляет данные на локальный API"""
    try:
        response = requests.post(
            LOCAL_API_URL,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=5
        )

        print(f"📤 Отправлено на локальный API: {data['action']}")
        print(f"📡 Status Code: {response.status_code}")
        if response.text:
            print(f"📋 Response: {response.text}")
        print("=" * 50)

    except requests.exceptions.ConnectionError:
        print("❌ Локальный API недоступен. Запустите local_api.py")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка отправки на локальный API: {e}")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже."
            )
        except:
            pass


def start_bot():
    """Запуск бота"""
    print("🤖 Запуск Telegram бота...")

    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота
    print("✅ Бот запущен. Ожидаем сообщения...")
    print(f"🌐 WebApp URL: {LOCAL_WEBAPP_URL}")
    print(f"🔌 API URL: {LOCAL_API_URL}")
    application.run_polling(allowed_updates=Update.ALL_TYPES)