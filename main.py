import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CallbackContext  # Adicionei esta importação
)
from config.config import Config
from handlers import images
from handlers import commands, expenses
from database.db import create_table
from handlers.commands import handle_exit
from keyboards.inline import get_main_keyboard  # Importe o teclado
from config.languages import translations  # Importe as traduções

app = Application.builder().token(Config.TOKEN).build()

async def handle_language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    language = query.data.split('_')[-1]
    context.user_data['language'] = language
    
    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=translations[language]['language_set'],
        reply_markup=get_main_keyboard(language)
    )

# Registro de handlers
app.add_handler(CommandHandler("start", commands.start))
app.add_handler(CallbackQueryHandler(commands.handle_exit, pattern="^exit$"))
app.add_handler(CallbackQueryHandler(expenses.handle_enter_value, pattern="^enter_value$"))
app.add_handler(CallbackQueryHandler(commands.handle_language_change, pattern="^change_language$"))
app.add_handler(CallbackQueryHandler(handle_language_selection, pattern="^set_language_"))
app.add_handler(CallbackQueryHandler(commands.handle_post_registration, pattern="^(register_again|back_to_main)$"))
app.add_handler(CallbackQueryHandler(images.handle_send_image, pattern="^send_image$"))  # Novo
app.add_handler(MessageHandler(filters.PHOTO, images.receive_image))  # Novo
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, expenses.save_expense))
app.add_handler(CallbackQueryHandler(expenses.handle_buttons))

IMAGE_FOLDER = "receipts"
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

if __name__ == "__main__":
    create_table()
    print("[STATUS] Bot iniciado!")
    app.run_polling(drop_pending_updates=True)