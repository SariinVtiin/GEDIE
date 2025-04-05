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
       
from handlers import cards

app = Application.builder().token(Config.TOKEN).build()

async def handle_language_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    # →→→ Garanta que a extração retorne uma string ←←←
    language = query.data.split('_')[-1]  # Retorna 'pt' ou 'en' (string)
    context.user_data['language'] = language  # Armazena como string
    
    await query.message.delete()
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=translations[language]['language_set'],  # Agora usa string
        reply_markup=get_main_keyboard(language)
    )

# Handlers principais
app.add_handler(CommandHandler("start", commands.start))

# Handlers de CallbackQuery (ESPECÍFICOS primeiro)
app.add_handler(CallbackQueryHandler(commands.handle_exit, pattern="^exit$"))
app.add_handler(CallbackQueryHandler(expenses.handle_enter_value, pattern="^enter_value$"))
app.add_handler(CallbackQueryHandler(cards.start_add_card, pattern="^add_credit_card$"))
app.add_handler(CallbackQueryHandler(commands.handle_language_change, pattern="^change_language$"))
app.add_handler(CallbackQueryHandler(commands.handle_settings, pattern="^open_settings$"))
app.add_handler(CallbackQueryHandler(handle_language_selection, pattern="^set_language_"))
app.add_handler(CallbackQueryHandler(commands.handle_post_registration, pattern="^(register_again|back_to_main)$"))
app.add_handler(CallbackQueryHandler(images.handle_send_image, pattern="^send_image$"))
app.add_handler(CallbackQueryHandler(expenses.skip_description, pattern="^skip_description$"))
app.add_handler(CallbackQueryHandler(cards.list_cards, pattern="^list_cards$"))

# Handler genérico de CallbackQuery (SEM pattern, por último)
app.add_handler(CallbackQueryHandler(expenses.handle_buttons))  # Categorias

# Handlers de Message (ordem: específico → genérico)
app.add_handler(MessageHandler(filters.PHOTO, images.receive_image))  # Fotos primeiro
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d{4}'), cards.handle_card_input))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, expenses.save_expense))  # Texto único

IMAGE_FOLDER = "receipts"
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

if __name__ == "__main__":
    create_table()
    print("[STATUS] Bot iniciado!")
    app.run_polling(drop_pending_updates=True)