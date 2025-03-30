from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  
from telegram.ext import CallbackContext
from keyboards.inline import get_main_keyboard
from config.languages import translations

async def start(update: Update, context: CallbackContext):
    language = context.user_data.get('language', 'pt')
    await update.message.reply_text(
        translations[language]['greeting'],
        reply_markup=get_main_keyboard(language)
    )

async def handle_language_change(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    language = context.user_data.get('language', 'pt')
    
    keyboard = [
        [InlineKeyboardButton("Português 🇧🇷", callback_data="set_language_pt")],
        [InlineKeyboardButton("English 🇺🇸", callback_data="set_language_en")]
    ]
    
    await query.message.reply_text(
        translations[language]['language_prompt'],
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.message.delete()

async def handle_post_registration(update: Update, context: CallbackContext):
    """Gerencia o menu pós-registro"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "register_again":
        context.user_data['awaiting_amount'] = True  # Habilita entrada de novo valor
        await query.message.reply_text("💰 Digite o novo valor:")
        
    elif query.data == "back_to_main":
        context.user_data.clear()  # Limpa TODOS os dados anteriores
        await query.message.reply_text(
            "🏠 Menu principal:",
            reply_markup=get_main_keyboard()  # Reenvia o teclado principal
        )
    
    await query.message.delete()  # Remove a mensagem antiga

async def handle_exit(update: Update, context: CallbackContext):
    """Encerra a interação e limpa o contexto"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text("👋 Até logo! Use /start para reiniciar.")
    context.user_data.clear()  # Limpa todos os dados do usuário
    await query.message.delete()  # Remove a mensagem com os botões