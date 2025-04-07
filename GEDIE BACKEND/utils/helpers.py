from telegram import Update

def send_message(update: Update, text: str):
    update.message.reply_text(text)
