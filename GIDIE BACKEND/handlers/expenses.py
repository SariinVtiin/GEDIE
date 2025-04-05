from telegram import Update
from telegram.ext import CallbackContext
from database.db import insert_expense
from keyboards.inline import get_categories_keyboard, get_post_registration_keyboard, get_description_keyboard
from config.languages import translations
from keyboards.inline import get_main_keyboard

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
            category=query.data,
            description=context.user_data.get('description', "")
        )
        
        if success:
            context.user_data.clear()  # Limpeza total
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"✅ {translations[language]['saved_expense']}",
                reply_markup=get_main_keyboard(language)  # Adicionado
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
    
    context.user_data.clear()

async def handle_enter_value(update: Update, context: CallbackContext):
    """Solicita valor com exemplo integrado"""
    query = update.callback_query
    await query.answer()
    language = context.user_data.get('language', 'pt')
    
    await query.message.reply_text(
        "💵 *Digite o valor e descrição (opcional):*\n"
        "Exemplo: `958.80 Almoço` ou `100,50`",
        parse_mode="Markdown"
    )
    context.user_data['awaiting_input'] = True  # Novo estado
    await query.message.delete()

async def save_expense(update: Update, context: CallbackContext):
    """Processa valor e descrição em uma única mensagem"""
    language = context.user_data.get('language', 'pt')
    user_input = update.message.text.strip()
    
    try:
        # Separa valor e descrição pelo primeiro espaço
        parts = user_input.split(maxsplit=1)
        amount_str = parts[0].replace(',', '.')  # Suporta ambas as notações decimais
        
        # Converte para float
        amount = float(amount_str)
        description = parts[1] if len(parts) > 1 else ""
        
        # Armazena no contexto
        context.user_data['amount'] = amount
        context.user_data['description'] = description
        
        # Mostra categorias
        await update.message.reply_text(
            translations[language]['select_category'],
            reply_markup=get_categories_keyboard(language)
        )
        context.user_data['awaiting_category'] = True
        
    except ValueError:
        await update.message.reply_text(translations[language]['invalid_format'])
        context.user_data.clear()

async def handle_description(update: Update, context: CallbackContext):
    """Processa a descrição APENAS se estiver no estado correto"""
    if not context.user_data.get('awaiting_description'):
        return  # Ignora se não for a etapa esperada
    
    language = context.user_data.get('language', 'pt')
    context.user_data['description'] = update.message.text
    context.user_data['awaiting_category'] = True  # Novo estado
    
    await update.message.reply_text(
        translations[language]['select_category'],
        reply_markup=get_categories_keyboard(language)
    )

async def skip_description(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    language = context.user_data.get('language', 'pt')
    
    try:
        # Remove a mensagem original
        await query.message.delete()
        
        # Envia novo teclado de categorias
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=translations[language]['select_category'],
            reply_markup=get_categories_keyboard(language)
        )
        context.user_data['awaiting_category'] = True
        context.user_data['description'] = ""  # Descrição vazia
        
    except Exception as e:
        print(f"Erro ao pular descrição: {str(e)}")