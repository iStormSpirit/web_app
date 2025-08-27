import logging
import requests
from telegram import Update, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import json
from urllib.parse import urlparse, parse_qs
import asyncio

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация - ИСПОЛЬЗУЕМ ЛОКАЛЬНЫЙ СЕРВЕР!
BOT_TOKEN = "8222846517:AAEVXzNlrt14BWIK2QrA38JE72doZ2Fy3YE"  # Замените на токен вашего бота
LOCAL_API_URL = "http://localhost:8000/api"
LOCAL_WEBAPP_URL = "http://localhost:8080/webapp.html"

# Глобальная переменная для хранения initData
user_init_data = {}


def get_main_keyboard():
    """Клавиатура с кнопкой авторизации"""
    keyboard = [
        [KeyboardButton("🔐 Авторизоваться", web_app=WebAppInfo(url=LOCAL_WEBAPP_URL))],
        [KeyboardButton("📋 Показать мои данные")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите действие...")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 Добро пожаловать!\n\n"
        "Этот бот работает в локальном режиме.\n"
        "Нажмите 'Авторизоваться' для имитации WebApp.\n"
        "Или просто напишите любое сообщение!"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

    await send_to_local_api({
        "action": "start_command",
        "user_id": update.effective_user.id,
        "username": update.effective_user.username,
        "first_name": update.effective_user.first_name,
        "chat_id": update.effective_chat.id
    })


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений"""
    user = update.effective_user
    message = update.message

    # Если пользователь нажал "Показать мои данные"
    if message.text == "📋 Показать мои данные":
        if str(user.id) in user_init_data:
            data = user_init_data[str(user.id)]
            response_text = (
                f"📊 Ваши данные:\n"
                f"👤 ID: {user.id}\n"
                f"📛 Имя: {user.first_name}\n"
                f"🔗 Username: @{user.username or 'нет'}\n"
                f"💾 InitData сохранен: Да"
            )
        else:
            response_text = "❌ Данные авторизации еще не получены. Нажмите 'Авторизоваться'."

        await message.reply_text(response_text, reply_markup=get_main_keyboard())
        return

    # Обычное сообщение
    print("📨 Сообщение:", message.text)

    message_data = {
        "action": "message",
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "chat_id": message.chat_id,
        "text": message.text,
        "timestamp": message.date.isoformat()
    }

    await send_to_local_api(message_data)
    await message.reply_text("✅ Сообщение получено!", reply_markup=get_main_keyboard())


async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик данных из Web App"""
    try:
        web_app_data = update.effective_message.web_app_data
        user_id = update.effective_user.id

        print("🎯 WebApp данные:", web_app_data.data)

        # Сохраняем данные пользователя
        user_init_data[str(user_id)] = {
            "raw_data": web_app_data.data,
            "parsed_data": parse_init_data(web_app_data.data),
            "timestamp": update.message.date.isoformat()
        }

        # Отправляем на API
        await send_to_local_api({
            "action": "webapp_auth",
            "user_id": user_id,
            "init_data": user_init_data[str(user_id)],
            "chat_id": update.effective_chat.id
        })

        await update.message.reply_text(
            "✅ Данные авторизации получены и сохранены локально!",
            reply_markup=get_main_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка WebApp: {e}")
        await update.message.reply_text("❌ Ошибка обработки данных")


def parse_init_data(raw_data: str) -> dict:
    """Парсит initData"""
    result = {"raw": raw_data}
    try:
        if 'user=' in raw_data:
            # Пытаемся извлечь данные пользователя
            parts = raw_data.split('&')
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    result[key] = value
                    if key == 'user':
                        try:
                            result['user_obj'] = json.loads(value)
                        except:
                            pass
    except Exception as e:
        result["error"] = str(e)
    return result


async def send_to_local_api(data: dict):
    """Отправка данных на локальный API"""
    try:
        response = requests.post(
            LOCAL_API_URL,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=3
        )
        print(f"📤 API: {data['action']} - Status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠️  Локальный API недоступен (запустите local_api.py)")
    except Exception as e:
        print(f"❌ Ошибка API: {e}")


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")


def start_bot():
    """Запуск бота"""
    print("🤖 Запуск бота в ЛОКАЛЬНОМ режиме...")
    print("📍 WebApp URL:", LOCAL_WEBAPP_URL)
    print("🔌 API URL:", LOCAL_API_URL)
    print("💡 Совет: Запустите local_api.py и local_web_server.py")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

    application.add_error_handler(error_handler)

    print("✅ Бот запущен! Ожидаем сообщения...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    start_bot()