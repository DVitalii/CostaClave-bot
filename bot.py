import os
import logging
from telegram import Update, InputFile
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import anthropic

# ── Настройки ──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"
MAX_HISTORY = 20          # максимум сообщений в истории на пользователя
SYSTEM_PROMPT = (
    "Ты полезный ассистент. Отвечай кратко и по делу. "
    "Если пользователь пишет на русском — отвечай на русском."
)
# ───────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Хранилище истории: { user_id: [ {"role": ..., "content": ...}, ... ] }
conversation_history: dict[int, list[dict]] = {}


def get_history(user_id: int) -> list[dict]:
    return conversation_history.setdefault(user_id, [])


def add_to_history(user_id: int, role: str, content: str) -> None:
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    # Обрезаем до MAX_HISTORY сообщений
    if len(history) > MAX_HISTORY:
        conversation_history[user_id] = history[-MAX_HISTORY:]


def ask_claude(user_id: int, user_text: str) -> str:
    add_to_history(user_id, "user", user_text)
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=get_history(user_id),
        )
        reply = response.content[0].text
        add_to_history(user_id, "assistant", reply)
        return reply
    except anthropic.APIError as e:
        logger.error("Anthropic API error: %s", e)
        return f"⚠️ Ошибка при обращении к Claude: {e}"


# ── Команды ────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    conversation_history.pop(user.id, None)   # сброс истории
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я чат-бот на базе Claude AI. Просто напиши мне что-нибудь.\n\n"
        "Команды:\n"
        "/start — начать заново\n"
        "/clear — очистить историю\n"
        "/help  — справка\n"
        "/about — о боте"
    )


async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conversation_history.pop(update.effective_user.id, None)
    await update.message.reply_text("🗑 История разговора очищена.")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ *Справка*\n\n"
        "Просто отправь мне текстовое сообщение — я отвечу с помощью Claude AI.\n\n"
        "Также можешь отправить *фото или документ* — я скажу, что получил файл.\n\n"
        "Команды:\n"
        "/start — начать заново и сбросить историю\n"
        "/clear — очистить историю\n"
        "/help  — эта справка\n"
        "/about — о боте",
        parse_mode="Markdown",
    )


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *О боте*\n\n"
        f"Модель: `{MODEL}`\n"
        f"Макс. история: {MAX_HISTORY} сообщений\n\n"
        "Создан с использованием:\n"
        "• [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)\n"
        "• [Anthropic Python SDK](https://github.com/anthropic/anthropic-sdk-python)",
        parse_mode="Markdown",
        disable_web_page_preview=True,
    )


# ── Обработчики сообщений ──────────────────────────────────────────────────

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    reply = ask_claude(user_id, user_text)
    await update.message.reply_text(reply)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caption = update.message.caption or "(без подписи)"
    await update.message.reply_text(
        f"📷 Получил фото!\nПодпись: {caption}\n\n"
        "К сожалению, анализ изображений в этом боте пока не поддерживается. "
        "Напиши текстовый вопрос — отвечу с удовольствием!"
    )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc = update.message.document
    caption = update.message.caption or "(без подписи)"
    await update.message.reply_text(
        f"📎 Получил файл: *{doc.file_name}*\n"
        f"Размер: {doc.file_size:,} байт\n"
        f"Подпись: {caption}\n\n"
        "Анализ файлов пока не поддерживается — задай вопрос текстом!",
        parse_mode="Markdown",
    )


# ── Запуск ─────────────────────────────────────────────────────────────────

def main() -> None:
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("clear", cmd_clear))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("about", cmd_about))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    logger.info("Бот запущен. Нажми Ctrl+C для остановки.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
