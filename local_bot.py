import logging
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
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

# Конфигурация
BOT_TOKEN = "8222846517:AAEVXzNlrt14BWIK2QrA38JE72doZ2Fy3YE"  # Ваш токен
LOCAL_API_URL = "http://localhost:8000/api"

# Глобальная переменная для хранения initData
user_init_data = {}


def get_main_keyboard():
    """Клавиатура без WebApp кнопки"""
    keyboard = [
        [KeyboardButton("🔐 Имитировать авторизацию")],
        [KeyboardButton("📋 Показать мои данные")],
        [KeyboardButton("👋 Привет!")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, input_field_placeholder="Выберите действие...")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = (
        "👋 Добро пожаловать!\n\n"
        "Этот бот работает в локальном режиме.\n"
        "Используйте кнопки для взаимодействия:\n"
        "• 🔐 Имитировать авторизацию\n"
        "• 📋 Показать мои данные\n"
        "• 👋 Просто поздороваться!"
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
    text = message.text

    print(f"📨 {user.first_name}: {text}")

    # Обработка кнопок
    if text == "🔐 Имитировать авторизацию":
        await handle_auth_simulation(update, user)

    elif text == "📋 Показать мои данные":
        await handle_show_data(update, user)

    elif text == "👋 Привет!":
        await handle_hello(update, user)

    else:
        await handle_regular_message(update, user, text)


# async def handle_auth_simulation(update: Update, user):
#     """Имитация авторизации"""
#     # Создаем имитацию initData
#     simulated_init_data = {
#         "user": {
#             "id": user.id,
#             "first_name": user.first_name,
#             "last_name": user.last_name,
#             "username": user.username,
#             "language_code": user.language_code,
#             "is_premium": getattr(user, 'is_premium', False)
#         },
#         "auth_date": update.message.date.timestamp(),
#         "hash": f"simulated_hash_{user.id}_{update.message.date.timestamp()}"
#     }
#
#     # Сохраняем данные
#     user_init_data[str(user.id)] = {
#         "simulated_data": simulated_init_data,
#         "timestamp": update.message.date.isoformat()
#     }
#
#     # Отправляем на API
#     await send_to_local_api({
#         "action": "auth_simulation",
#         "user_id": user.id,
#         "init_data": simulated_init_data,
#         "chat_id": update.effective_chat.id
#     })
#
#     await update.message.reply_text(
#         "✅ Авторизация имитирована!\n"
#         "Данные сохранены локально и отправлены на API.",
#         reply_markup=get_main_keyboard()
#     )
async def handle_auth_simulation(update: Update, user):
    """Имитация авторизации"""
    # Создаем имитацию initData
    simulated_init_data = {
        "user": {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "language_code": user.language_code,
            "is_premium": getattr(user, 'is_premium', False),
            "is_bot": user.is_bot
        },
        "auth_date": int(update.message.date.timestamp()),
        "hash": f"simulated_hash_{user.id}_{int(update.message.date.timestamp())}",
        "query_id": f"query_{user.id}_{int(update.message.date.timestamp())}",
        "auth_type": "telegram",
        "platform": "web"
    }

    # Сохраняем данные
    user_init_data[str(user.id)] = {
        "simulated_data": simulated_init_data,
        "timestamp": update.message.date.isoformat(),
        "raw_data_string": f"user={json.dumps(simulated_init_data['user'])}&auth_date={simulated_init_data['auth_date']}&hash={simulated_init_data['hash']}"
    }

    # Отправляем на API
    await send_to_local_api({
        "action": "auth_simulation",
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "chat_id": update.effective_chat.id,
        "init_data": user_init_data[str(user.id)],
        "timestamp": update.message.date.isoformat()
    })

    await update.message.reply_text(
        "✅ Авторизация имитирована!\n"
        "Данные сохранены локально и отправлены на API.",
        reply_markup=get_main_keyboard()
    )


async def handle_show_data(update: Update, user):
    """Показать данные пользователя"""
    user_id_str = str(user.id)

    if user_id_str in user_init_data:
        data = user_init_data[user_id_str]
        response_text = (
            f"📊 Ваши данные:\n"
            f"👤 ID: {user.id}\n"
            f"📛 Имя: {user.first_name}\n"
            f"🔗 Username: @{user.username or 'нет'}\n"
            f"💾 Данные авторизации: Сохранены\n"
            f"⏰ Время: {data['timestamp']}"
        )
    else:
        response_text = (
            f"👤 ID: {user.id}\n"
            f"📛 Имя: {user.first_name}\n"
            f"🔗 Username: @{user.username or 'нет'}\n"
            f"❌ Данные авторизации: Не получены\n"
            f"Нажмите '🔐 Имитировать авторизацию'"
        )

    await update.message.reply_text(response_text, reply_markup=get_main_keyboard())


async def handle_hello(update: Update, user):
    """Обработка приветствия"""
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n"
        f"Рад тебя видеть! 😊",
        reply_markup=get_main_keyboard()
    )

    await send_to_local_api({
        "action": "hello",
        "user_id": user.id,
        "username": user.username,
        "chat_id": update.effective_chat.id
    })


async def handle_regular_message(update: Update, user, text):
    """Обработка обычных сообщений"""
    message_data = {
        "action": "message",
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "chat_id": update.effective_chat.id,
        "text": text,
        "timestamp": update.message.date.isoformat()
    }

    await send_to_local_api(message_data)
    await update.message.reply_text(
        "✅ Сообщение получено и отправлено на API!",
        reply_markup=get_main_keyboard()
    )


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
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуйте позже.",
                reply_markup=get_main_keyboard()
            )
        except:
            pass


def start_bot():
    """Запуск бота"""
    print("🤖 Запуск бота в ЛОКАЛЬНОМ режиме...")
    print("🔌 API URL:", LOCAL_API_URL)
    print("💡 Кнопки будут работать без WebApp!")

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_error_handler(error_handler)

    print("✅ Бот запущен! Ожидаем сообщения...")
    print("📋 Доступные кнопки:")
    print("   • 🔐 Имитировать авторизацию")
    print("   • 📋 Показать мои данные")
    print("   • 👋 Привет!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    start_bot()