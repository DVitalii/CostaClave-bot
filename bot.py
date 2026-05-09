import os
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
Application, CommandHandler, MessageHandler,
filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("costaclave")

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

WAITING_NAME, WAITING_PHONE, WAITING_ADDRESS, WAITING_PROBLEM = range(4)

def detect_lang(update):
    lang = update.effective_user.language_code or "es"
    if lang.startswith("ru"):
        return "ru"
    elif lang.startswith("en"):
        return "en"
    elif lang.startswith("fr"):
        return "fr"
    else:
        return "es"

TEXTS = {
"welcome": {
"ru": "Dobro pozhalovat v CostaClave!\n\nMy - sluzhba srochnogo vskrytiya zamkov na Kosta-Blanka. Rabotaem 24/7.\n\nChto vas interesuet?",
"es": "Bienvenido a CostaClave!\n\nSomos el servicio de cerrajeria urgente en la Costa Blanca. Trabajamos 24/7.\n\nEn que podemos ayudarle?",
"en": "Welcome to CostaClave!\n\nWe are the emergency locksmith service on the Costa Blanca. Available 24/7.\n\nHow can we help you?",
"fr": "Bienvenue chez CostaClave!\n\nNous sommes le service de serrurerie d urgence sur la Costa Blanca. Disponible 24h/24.\n\nComment puis-je vous aider?",
},
"menu": {
"ru": ["Vyzvat mastera", "Tseny", "Zona raboty", "Vremya raboty", "Kontakty"],
"es": ["Pedir servicio", "Precios", "Zona de trabajo", "Horario", "Contacto"],
"en": ["Book a locksmith", "Prices", "Service area", "Working hours", "Contact"],
"fr": ["Appeler un serrurier", "Prix", "Zone intervention", "Horaires", "Contact"],
},
"prices": {
"ru": "Nashi tseny:\n\nOtkrytie zamka - ot 60 evro\nVskrytie avto - ot 80 evro\nZamena zamka - ot 90 evro\nNochnoy vyzov - +20 evro",
"es": "Nuestros precios:\n\nApertura de cerradura - desde 60 euros\nApertura de coche - desde 80 euros\nCambio de cerradura - desde 90 euros\nServicio nocturno - +20 euros",
"en": "Our prices:\n\nLock opening - from 60 euro\nCar opening - from 80 euro\nLock replacement - from 90 euro\nNight call - +20 euro",
"fr": "Nos tarifs:\n\nOuverture de serrure - a partir de 60 euros\nOuverture de voiture - a partir de 80 euros\nRemplacement - a partir de 90 euros\nAppel nocturne - +20 euros",
},
"area": {
"ru": "Zona obsluzhivaniya:\n\nDeniya, Khavea, Morayra, Benissa, Kalpe, Altea, Benidorm, Gandiya\n\nVes rayon Kosta-Blanka Norte.",
"es": "Zona de trabajo:\n\nDenia, Javea, Moraira, Benissa, Calpe, Altea, Benidorm, Gandia\n\nToda la Costa Blanca Norte.",
"en": "Service area:\n\nDenia, Javea, Moraira, Benissa, Calpe, Altea, Benidorm, Gandia\n\nAll Costa Blanca Norte.",
"fr": "Zone intervention:\n\nDenia, Javea, Moraira, Benissa, Calpe, Altea, Benidorm, Gandia\n\nToute la Costa Blanca Norte.",
},
"hours": {
"ru": "Vremya raboty:\n\n24 chasa v sutki\n7 dney v nedelyu\n365 dney v godu\n\nDazhe v prazdniki i nochyu!",
"es": "Horario:\n\n24 horas al dia\n7 dias a la semana\n365 dias al ano\n\nIncluso en festivos y de noche!",
"en": "Working hours:\n\n24 hours a day\n7 days a week\n365 days a year\n\nEven on holidays and at night!",
"fr": "Horaires:\n\n24h/24\n7j/7\n365 jours par an\n\nMeme les jours feries et la nuit!",
},
"contact": {
"ru": "Kontakty CostaClave:\n\nWhatsApp/Telegram: +34 XXX XXX XXX\ncostaclave.net\ninfo@costaclave.net",
"es": "Contacto CostaClave:\n\nWhatsApp/Telegram: +34 XXX XXX XXX\ncostaclave.net\ninfo@costaclave.net",
"en": "CostaClave contacts:\n\nWhatsApp/Telegram: +34 XXX XXX XXX\ncostaclave.net\ninfo@costaclave.net",
"fr": "Contact CostaClave:\n\nWhatsApp/Telegram: +34 XXX XXX XXX\ncostaclave.net\ninfo@costaclave.net",
},
"ask_name": {
"ru": "Davajte oformim zayavku. Kak vas zovut?",
"es": "Vamos a registrar su solicitud. Como se llama?",
"en": "Let us register your request. What is your name?",
"fr": "Enregistrons votre demande. Comment vous appelez-vous?",
},
"ask_phone": {
"ru": "Ukazhite vash nomer telefona:",
"es": "Indique su numero de telefono:",
"en": "Please share your phone number:",
"fr": "Indiquez votre numero de telephone:",
},
"ask_address": {
"ru": "Ukazhite adres ili naselyonnyy punkt:",
"es": "Indique su direccion o localidad:",
"en": "Please provide your address or location:",
"fr": "Indiquez votre adresse ou localite:",
},
"ask_problem": {
"ru": "Opishite problemu (naprimer: zakrylsya v kvartire, ne otkryvaetsya zamok):",
"es": "Describa el problema (por ejemplo: se quedo fuera, la cerradura no abre):",
"en": "Describe the problem (e.g.: locked out, lock won’t open):",
"fr": "Decrivez le probleme (par ex: porte claquee, serrure bloquee):",
},
"done": {
"ru": "Zayavka prinyata! Master svyazhetsya s vami v blizhaishie minuty. Spasibo za vybor CostaClave!",
"es": "Solicitud recibida! El tecnico le contactara en pocos minutos. Gracias por elegir CostaClave!",
"en": "Request received! Our locksmith will contact you within minutes. Thank you for choosing CostaClave!",
"fr": "Demande recue! Notre serrurier vous contactera dans quelques minutes. Merci d avoir choisi CostaClave!",
},
"cancel": {
"ru": "Zayavka otmenena. Esli ponadobitsya - nazhmite /start",
"es": "Solicitud cancelada. Si necesita ayuda pulse /start",
"en": "Request cancelled. If you need help press /start",
"fr": "Demande annule. Si vous avez besoin d aide appuyez sur /start",          
},
}

def get_text(key, lang):
    return TEXTS[key].get(lang, TEXTS[key]["es"])

def get_menu(lang):
    buttons = [[btn] for btn in TEXTS["menu"][lang]]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

async def start(update, context):
    lang = detect_lang(update)
    context.user_data["lang"] = lang
    await update.message.reply_text(get_text("welcome", lang), reply_markup=get_menu(lang))

async def handle_menu(update, context):
    lang = context.user_data.get("lang", detect_lang(update))
    text = update.message.text
    menu_items = TEXTS["menu"]


if text in [menu_items[l][0] for l in menu_items]:
    context.user_data["lang"] = lang
    await update.message.reply_text(get_text("ask_name", lang))
    return WAITING_NAME
elif text in [menu_items[l][1] for l in menu_items]:
    await update.message.reply_text(get_text("prices", lang))
elif text in [menu_items[l][2] for l in menu_items]:
    await update.message.reply_text(get_text("area", lang))
elif text in [menu_items[l][3] for l in menu_items]:
    await update.message.reply_text(get_text("hours", lang))
elif text in [menu_items[l][4] for l in menu_items]:
    await update.message.reply_text(get_text("contact", lang))
else:
    await update.message.reply_text(get_text("welcome", lang), reply_markup=get_menu(lang))

return ConversationHandler.END


async def get_name(update, context):
    context.user_data["name"] = update.message.text
    lang = context.user_data.get("lang", "es")
    phone_button = ReplyKeyboardMarkup(
    [[KeyboardButton("Share phone number", request_contact=True)]],
    resize_keyboard=True, one_time_keyboard=True
)
    await update.message.reply_text(get_text("ask_phone", lang), reply_markup=phone_button)
    return WAITING_PHONE

async def get_phone(update, context):
    if update.message.contact:
    context.user_data["phone"] = update.message.contact.phone_number
else:
    context.user_data["phone"] = update.message.text
    lang = context.user_data.get("lang", "es")
    await update.message.reply_text(get_text("ask_address", lang))
    return WAITING_ADDRESS

async def get_address(update, context):
    context.user_data["address"] = update.message.text
    lang = context.user_data.get("lang", "es")
    await update.message.reply_text(get_text("ask_problem", lang))
    return WAITING_PROBLEM

async def get_problem(update, context):
    context.user_data["problem"] = update.message.text
    lang = context.user_data.get("lang", "es")
    user = update.effective_user


admin_msg = (
    "NOVAYA ZAYAVKA - CostaClave\n\n"
    "Imya: " + str(context.user_data.get("name", "-")) + "\n"
    "Telefon: " + str(context.user_data.get("phone", "-")) + "\n"
    "Adres: " + str(context.user_data.get("address", "-")) + "\n"
    "Problema: " + str(context.user_data.get("problem", "-")) + "\n"
    "Yazyk: " + lang.upper() + "\n"
    "Telegram ID: " + str(user.id)
)

try:
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_msg)
except Exception as e:
    logger.error("Ne udalos otpravit uvedomlenie: " + str(e))

await update.message.reply_text(get_text("done", lang), reply_markup=get_menu(lang))
return ConversationHandler.END
```

async def cancel(update, context):
lang = context.user_data.get("lang", "es")
await update.message.reply_text(get_text("cancel", lang), reply_markup=get_menu(lang))
return ConversationHandler.END

def main():
app = Application.builder().token(BOT_TOKEN).build()

```
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

logger.info("CostaClave bot zapushchen!")
app.run_polling()
```

if **name** == "**main**":
main()
