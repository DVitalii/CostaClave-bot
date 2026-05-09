import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === НАСТРОЙКИ ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "ВСТАВЬ_СВОЙ_ТОКЕН_ЗДЕСЬ")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "ВСТАВЬ_СВОЙ_CHAT_ID")

# === СОСТОЯНИЯ ДИАЛОГА ===
WAITING_NAME, WAITING_PHONE, WAITING_ADDRESS, WAITING_PROBLEM = range(4)

# === ОПРЕДЕЛЕНИЕ ЯЗЫКА ===
def detect_lang(update: Update) -> str:
    lang = update.effective_user.language_code or "es"
    if lang.startswith("ru"):
        return "ru"
    elif lang.startswith("en"):
        return "en"
    elif lang.startswith("fr"):
        return "fr"
    else:
        return "es"

# === ТЕКСТЫ НА РАЗНЫХ ЯЗЫКАХ ===
TEXTS = {
    "welcome": {
        "ru": "🔐 Добро пожаловать в CostaClave!\n\nМы — служба срочного вскрытия замков на Коста-Бланка. Работаем 24/7.\n\nЧто вас интересует?",
        "es": "🔐 ¡Bienvenido a CostaClave!\n\nSomos el servicio de cerrajería urgente en la Costa Blanca. Trabajamos 24/7.\n\n¿En qué podemos ayudarle?",
        "en": "🔐 Welcome to CostaClave!\n\nWe are the emergency locksmith service on the Costa Blanca. Available 24/7.\n\nHow can we help you?",
        "fr": "🔐 Bienvenue chez CostaClave!\n\nNous sommes le service de serrurerie d'urgence sur la Costa Blanca. Disponible 24h/24.\n\nComment puis-je vous aider?",
    },
    "menu": {
        "ru": ["📋 Вызвать мастера", "💰 Цены", "📍 Зона работы", "⏰ Время работы", "📞 Контакты"],
        "es": ["📋 Pedir servicio", "💰 Precios", "📍 Zona de trabajo", "⏰ Horario", "📞 Contacto"],
        "en": ["📋 Book a locksmith", "💰 Prices", "📍 Service area", "⏰ Working hours", "📞 Contact"],
        "fr": ["📋 Appeler un serrurier", "💰 Prix", "📍 Zone d'intervention", "⏰ Horaires", "📞 Contact"],
    },
    "prices": {
        "ru": "💰 *Наши цены:*\n\n🔓 Открытие замка — от 60€\n🚗 Вскрытие авто — от 80€\n🔧 Замена замка — от 90€\n🚨 Ночной вызов (+22:00) — +20€\n\n_Точная стоимость после осмотра. Без скрытых доплат._",
        "es": "💰 *Nuestros precios:*\n\n🔓 Apertura de cerradura — desde 60€\n🚗 Apertura de coche — desde 80€\n🔧 Cambio de cerradura — desde 90€\n🚨 Servicio nocturno (+22:00) — +20€\n\n_Precio exacto tras inspección. Sin cargos ocultos._",
        "en": "💰 *Our prices:*\n\n🔓 Lock opening — from 60€\n🚗 Car opening — from 80€\n🔧 Lock replacement — from 90€\n🚨 Night call (+22:00) — +20€\n\n_Exact price after inspection. No hidden charges._",
        "fr": "💰 *Nos tarifs:*\n\n🔓 Ouverture de serrure — à partir de 60€\n🚗 Ouverture de voiture — à partir de 80€\n🔧 Remplacement de serrure — à partir de 90€\n🚨 Appel nocturne (+22:00) — +20€\n\n_Prix exact après inspection. Sans frais cachés._",
    },
    "area": {
        "ru": "📍 *Зона обслуживания:*\n\nДения, Хавеа, Морайра, Бенисса, Калпе, Альтеа, Бенидорм, Гандия\n\nВесь район Коста-Бланка Норте. Если сомневаетесь — спросите!",
        "es": "📍 *Zona de trabajo:*\n\nDénia, Jávea, Moraira, Benissa, Calpe, Altea, Benidorm, Gandía\n\nToda la Costa Blanca Norte. ¡Si tiene dudas, pregúntenos!",
        "en": "📍 *Service area:*\n\nDénia, Jávea, Moraira, Benissa, Calpe, Altea, Benidorm, Gandía\n\nAll Costa Blanca Norte. If in doubt — just ask!",
        "fr": "📍 *Zone d'intervention:*\n\nDénia, Jávea, Moraira, Benissa, Calpe, Altea, Benidorm, Gandía\n\nToute la Costa Blanca Norte. En cas de doute, demandez!",
    },
    "hours": {
        "ru": "⏰ *Время работы:*\n\n✅ 24 часа в сутки\n✅ 7 дней в неделю\n✅ 365 дней в году\n\nДаже в праздники и ночью — мы на связи!",
        "es": "⏰ *Horario:*\n\n✅ 24 horas al día\n✅ 7 días a la semana\n✅ 365 días al año\n\n¡Incluso en festivos y de noche — estamos disponibles!",
        "en": "⏰ *Working hours:*\n\n✅ 24 hours a day\n✅ 7 days a week\n✅ 365 days a year\n\nEven on holidays and at night — we're here!",
        "fr": "⏰ *Horaires:*\n\n✅ 24h/24\n✅ 7j/7\n✅ 365 jours par an\n\nMême les jours fériés et la nuit — nous sommes disponibles!",
    },
    "contact": {
        "ru": "📞 *Контакты CostaClave:*\n\n📱 WhatsApp/Telegram: +34 XXX XXX XXX\n🌐 costaclave.net\n📧 info@costaclave.net\n\nИли нажмите «Вызвать мастера» и мы перезвоним вам!",
        "es": "📞 *Contacto CostaClave:*\n\n📱 WhatsApp/Telegram: +34 XXX XXX XXX\n🌐 costaclave.net\n📧 info@costaclave.net\n\n¡O pulse «Pedir servicio» y le llamaremos!",
        "en": "📞 *CostaClave contacts:*\n\n📱 WhatsApp/Telegram: +34 XXX XXX XXX\n🌐 costaclave.net\n📧 info@costaclave.net\n\nOr press «Book a locksmith» and we'll call you back!",
        "fr": "📞 *Contact CostaClave:*\n\n📱 WhatsApp/Telegram: +34 XXX XXX XXX\n🌐 costaclave.net\n📧 info@costaclave.net\n\nOu appuyez sur «Appeler un serrurier» et nous vous rappellerons!",
    },
    "ask_name": {
        "ru": "📋 Отлично! Давайте оформим заявку.\n\nКак вас зовут?",
        "es": "📋 ¡Perfecto! Vamos a registrar su solicitud.\n\n¿Cómo se llama?",
        "en": "📋 Great! Let's register your request.\n\nWhat's your name?",
        "fr": "📋 Parfait! Enregistrons votre demande.\n\nComment vous appelez-vous?",
    },
    "ask_phone": {
        "ru": "📱 Укажите ваш номер телефона (или нажмите кнопку ниже):",
        "es": "📱 Indique su número de teléfono (o pulse el botón):",
        "en": "📱 Please share your phone number (or press the button below):",
        "fr": "📱 Indiquez votre numéro de téléphone (ou appuyez sur le bouton):",
    },
    "ask_address": {
        "ru": "📍 Укажите адрес или населённый пункт:",
        "es": "📍 Indique su dirección o localidad:",
        "en": "📍 Please provide your address or location:",
        "fr": "📍 Indiquez votre adresse ou localité:",
    },
    "ask_problem": {
        "ru": "🔐 Опишите проблему (например: закрылся в квартире, не открывается замок, сломался ключ):",
        "es": "🔐 Describa el problema (por ejemplo: se quedó fuera, la cerradura no abre, se rompió la llave):",
        "en": "🔐 Describe the problem (e.g.: locked out, lock won't open, key broke inside):",
        "fr": "🔐 Décrivez le problème (par ex: porte claquée, serrure bloquée, clé cassée):",
    },
    "done": {
        "ru": "✅ Заявка принята! Мастер свяжется с вами в ближайшие несколько минут.\n\nСпасибо, что выбрали CostaClave! 🔐",
        "es": "✅ ¡Solicitud recibida! El técnico le contactará en pocos minutos.\n\n¡Gracias por elegir CostaClave! 🔐",
        "en": "✅ Request received! Our locksmith will contact you within minutes.\n\nThank you for choosing CostaClave! 🔐",
        "fr": "✅ Demande reçue! Notre serrurier vous contactera dans quelques minutes.\n\nMerci d'avoir choisi CostaClave! 🔐",
    },
    "cancel": {
        "ru": "❌ Заявка отменена. Если понадоблюсь — нажмите /start",
        "es": "❌ Solicitud cancelada. Si necesita ayuda — pulse /start",
        "en": "❌ Request cancelled. If you need help — press /start",
        "fr": "❌ Demande annulée. Si vous avez besoin d'aide — appuyez sur /start",
    },
}

def get_text(key: str, lang: str) -> str:
    return TEXTS[key].get(lang, TEXTS[key]["es"])

def get_menu(lang: str) -> ReplyKeyboardMarkup:
    buttons = [[btn] for btn in TEXTS["menu"][lang]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# === КОМАНДА /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = detect_lang(update)
    context.user_data["lang"] = lang
    await update.message.reply_text(
        get_text("welcome", lang),
        reply_markup=get_menu(lang)
    )

# === ОБРАБОТКА МЕНЮ ===
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", detect_lang(update))
    text = update.message.text

    menu_items = TEXTS["menu"]

    if text in [menu_items[l][0] for l in menu_items]:  # Вызов мастера
        context.user_data["lang"] = lang
        await update.message.reply_text(get_text("ask_name", lang))
        return WAITING_NAME

    elif text in [menu_items[l][1] for l in menu_items]:  # Цены
        await update.message.reply_text(get_text("prices", lang), parse_mode="Markdown")

    elif text in [menu_items[l][2] for l in menu_items]:  # Зона работы
        await update.message.reply_text(get_text("area", lang), parse_mode="Markdown")

    elif text in [menu_items[l][3] for l in menu_items]:  # Время работы
        await update.message.reply_text(get_text("hours", lang), parse_mode="Markdown")

    elif text in [menu_items[l][4] for l in menu_items]:  # Контакты
        await update.message.reply_text(get_text("contact", lang), parse_mode="Markdown")

    else:
        await update.message.reply_text(get_text("welcome", lang), reply_markup=get_menu(lang))

    return ConversationHandler.END

# === ДИАЛОГ: ПРИЁМ ЗАЯВКИ ===
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    lang = context.user_data.get("lang", "es")
    phone_button = ReplyKeyboardMarkup(
        [[KeyboardButton("📱 Поделиться номером", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await update.message.reply_text(get_text("ask_phone", lang), reply_markup=phone_button)
    return WAITING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        context.user_data["phone"] = update.message.contact.phone_number
    else:
        context.user_data["phone"] = update.message.text
    lang = context.user_data.get("lang", "es")
    await update.message.reply_text(get_text("ask_address", lang), reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True))
    return WAITING_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    lang = context.user_data.get("lang", "es")
    await update.message.reply_text(get_text("ask_problem", lang))
    return WAITING_PROBLEM

async def get_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["problem"] = update.message.text
    lang = context.user_data.get("lang", "es")
    user = update.effective_user

    # Уведомление администратору
    admin_msg = (
        f"🆕 *НОВАЯ ЗАЯВКА — CostaClave*\n\n"
        f"👤 Имя: {context.user_data.get('name', '—')}\n"
        f"📱 Телефон: {context.user_data.get('phone', '—')}\n"
        f"📍 Адрес: {context.user_data.get('address', '—')}\n"
        f"🔐 Проблема: {context.user_data.get('problem', '—')}\n"
        f"🌐 Язык клиента: {lang.upper()}\n"
        f"💬 Telegram: @{user.username or '—'} (ID: {user.id})"
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_CHAT_ID,
            text=admin_msg,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление: {e}")

    await update.message.reply_text(get_text("done", lang), reply_markup=get_menu(lang))
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "es")
    await update.message.reply_text(get_text("cancel", lang), reply_markup=get_menu(lang))
    return ConversationHandler.END

# === ЗАПУСК ===
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            WAITING_PHONE: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
            WAITING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            WAITING_PROBLEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_problem)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    logger.info("CostaClave bot запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
