from telegram import Update
from telegram.ext import CallbackContext
from database.db import insert_expense
from keyboards.inline import get_categories_keyboard, get_post_registration_keyboard, get_description_keyboard
from config.languages import translations
from keyboards.inline import get_main_keyboard
from keyboards.inline import get_payment_method_keyboard

async def handle_buttons(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    language = context.user_data.get('language', 'pt')
    amount = context.user_data.get('amount')
    description = context.user_data.get('description', "")
    
    # Verifica se é uma categoria válida
    if not query.data.startswith("CATEGORY_"):
        return
    
    # Validação do valor
    if not amount:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=translations[language]['invalid_amount']
        )
        return
    
    try:
        # Armazena a categoria e solicita o método de pagamento
        context.user_data['category'] = query.data
        
        # →→→ Novo: Mostra opções de método de pagamento ←←←
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=translations[language]['select_payment_method'],
            reply_markup=get_payment_method_keyboard(language)
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

    if 'current_flow' in context.user_data:
        await update.message.reply_text(
            translations[language]['wrong_flow'],
            reply_markup=get_main_keyboard(language)
        )
        return

    language = context.user_data.get('language', 'pt')
    user_input = update.message.text.strip()
    
    try:
        # Separa valor e descrição pelo primeiro espaço
        parts = user_input.split(maxsplit=1)
        amount_str = parts[0].replace(',', '.')  # Suporta ambas as notações decimais
        
        # Converte para float
        amount = float(update.message.text.split()[0].replace(',', '.'))
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

async def handle_payment_method(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    language = context.user_data.get('language', 'pt')
    payment_method = query.data.split('_')[1]  # Ex: "card", "cash", "pix"
    
    try:
        # Recupera todos os dados do contexto
        user_data = context.user_data
        success = insert_expense(
            user_id=query.message.chat_id,
            amount=user_data['amount'],
            category=user_data['category'],
            description=user_data.get('description', ""),
            payment_method=payment_method  # Novo parâmetro
        )
        
        if success:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=translations[language]['saved_expense'].format(
                    amount=f"{user_data['amount']:.2f}",
                    category=user_data['category'].replace('CATEGORY_', ''),
                    payment_method=payment_method.upper()  # Novo campo
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
    
    context.user_data.clear()  # Limpa todos os dados