import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json

# Включаем логирование, чтобы видеть ошибки
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токены и ключи читаются из переменных окружения (их мы зададим позже на Railway)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

if not TELEGRAM_TOKEN:
    raise ValueError("Нет TELEGRAM_BOT_TOKEN!")
if not OPENROUTER_API_KEY:
    raise ValueError("Нет OPENROUTER_API_KEY!")

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот на основе DeepSeek. Задавай любой вопрос!")

# Команда /clear (очистить историю разговора)
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("История разговора очищена!")

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    # Покажем, что бот печатает (чтобы пользователь ждал)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Собираем историю сообщений (если есть)
    history = context.user_data.get("history", [])

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    # Получаем историю
    history = context.user_data.get("history", [])

    # Системный промпт
    SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Ты — профессиональный консультант по питанию и здоровому образу жизни. "
        "Отвечай дружелюбно, давай полезные советы по питанию, учитывай индивидуальные особенности. "
        "Если пользователь спрашивает не о питании, вежливо направляй его обратно к теме. "
        "Не давай медицинских диагнозов, всегда рекомендуй консультацию со специалистом при серьёзных вопросах.\n\n"
        "ВАЖНО: не используй в ответах markdown, звездочки, подчеркивания и другие символы форматирования. "
        "Отвечай обычным текстом без выделений."
    )
}
    # Вставляем системное сообщение, если его нет в начале
    if not history or history[0].get("role") != "system":
        history.insert(0, SYSTEM_PROMPT)

    # Добавляем новое сообщение пользователя
    history.append({"role": "user", "content": user_message})

    # Ограничиваем длину истории
    if len(history) > 10:
        history = history[-10:]

    # Запрос к OpenRouter
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": history
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        reply = data['choices'][0]['message']['content']

        history.append({"role": "assistant", "content": reply})
        context.user_data["history"] = history

        await update.message.reply_text(reply)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к OpenRouter: {e}")
        await update.message.reply_text("Произошла ошибка при обращении к нейросети. Попробуй позже.")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Ошибка парсинга ответа: {e}")
        await update.message.reply_text("Получен странный ответ от нейросети. Попробуй ещё раз.")
        
    # Добавляем новое сообщение пользователя в историю
    history.append({"role": "user", "content": user_message})

    # Ограничим длину истории, чтобы не переполнить контекст (например, последние 10 сообщений)
    if len(history) > 10:
        history = history[-10:]

    # Формируем запрос к OpenRouter (используем модель DeepSeek V3)
    payload = {
        "model": "deepseek/deepseek-chat",  # Можно сменить на другую модель
        "messages": history
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Отправляем запрос к OpenRouter
        response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
        data = response.json()
        reply = data['choices'][0]['message']['content']

        # Добавляем ответ ассистента в историю
        history.append({"role": "assistant", "content": reply})
        context.user_data["history"] = history

        # Отправляем ответ пользователю
        await update.message.reply_text(reply)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе к OpenRouter: {e}")
        await update.message.reply_text("Произошла ошибка при обращении к нейросети. Попробуй позже.")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Ошибка парсинга ответа: {e}")
        await update.message.reply_text("Получен странный ответ от нейросети. Попробуй ещё раз.")

# Функция, которая запускает бота
def main():
    # Создаём приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("clear", clear))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота (long polling)
    application.run_polling()

if __name__ == "__main__":

    main()







