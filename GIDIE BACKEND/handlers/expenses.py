from telegram import Update
from telegram.ext import CallbackContext
from database.db import insert_expense
from keyboards.inline import get_categories_keyboard, get_post_registration_keyboard
from config.languages import translations

async def save_expense(update: Update, context: CallbackContext):
    language = context.user_data.get('language', 'pt')
    
    try:
        amount = float(update.message.text.replace(',', '.'))
        context.user_data['amount'] = amount
        
        await update.message.reply_text(
            translations[language]['amount_prompt'],
            reply_markup=get_categories_keyboard(language)
        )
        
    except ValueError:
        await update.message.reply_text(translations[language]['invalid_amount'])
        context.user_data.clear()

async def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    language = context.user_data.get('language', 'pt')
    amount = context.user_data.get('amount')
    
    if not query.data.startswith("CATEGORY_"):
        return
    
    if not amount:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=translations[language]['invalid_amount']
        )
        return
    
    try:
        # REMOVIDO O receipt_path
        success = insert_expense(
            user_id=query.message.chat_id,
            amount=amount,
            category=query.data
        )
        
        if success:
            context.user_data.clear()  # Limpeza total
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=translations[language]['saved_expense'].format(
                    amount=f"{amount:.2f}", 
                    category=query.data.replace('CATEGORY_', '')
                ),
                reply_markup=get_post_registration_keyboard(language)
            )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=translations[language]['db_error']
            )
            
    except Exception as e:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=translations[language]['db_error']
        )

async def handle_enter_value(update: Update, context: CallbackContext):
    """Solicita explicitamente o valor da despesa"""
    query = update.callback_query
    await query.answer()
    
    # Mensagem clara + instrução
    await query.message.reply_text(
        "💵 *Digite o valor da despesa:*\n"
        "(Exemplos: 50, 25.99 ou 100,00)",
        parse_mode="Markdown"
    )
    context.user_data['awaiting_amount'] = True  # Marca o estado de espera
    
    await query.message.delete()  # Remove a mensagem anterior