from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from database.db import insert_expense, get_user_cards
from keyboards.inline import (
    get_categories_keyboard, 
    get_post_registration_keyboard, 
    get_description_keyboard,
    get_main_keyboard,
    get_payment_method_keyboard,
    get_user_cards_keyboard,    # Import this from inline.py instead
    get_card_registration_keyboard  # Import this from inline.py instead
)
from config.languages import translations

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
        # Se o método de pagamento for cartão, verificar se o usuário tem cartões cadastrados
        if payment_method == "card":
            # Busca os cartões do usuário
            user_cards = get_user_cards(query.message.chat_id)
            
            # Log para debug
            print(f"Cartões encontrados: {user_cards}")
            
            # Se não houver cartões cadastrados
            if not user_cards or len(user_cards) == 0:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=translations[language].get(
                        'no_cards', 
                        "Você não tem cartões cadastrados. Por favor, cadastre um cartão primeiro."
                    ),
                    reply_markup=get_card_registration_keyboard(language)
                )
                return
            
            # Se houver cartões, mostrar opções
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=translations[language].get('select_card', "Selecione o cartão:"),
                reply_markup=get_user_cards_keyboard(user_cards, language)
            )
            return
            
        # Continua normalmente para outros métodos de pagamento
        # Recupera todos os dados do contexto
        user_data = context.user_data
        success = insert_expense(
            user_id=query.message.chat_id,
            amount=user_data['amount'],
            category=user_data['category'],
            description=user_data.get('description', ""),
            payment_method=payment_method
        )
        
        if success:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=translations[language]['saved_expense'].format(
                    amount=f"{user_data['amount']:.2f}",
                    category=user_data['category'].replace('CATEGORY_', ''),
                    payment_method=payment_method.upper()
                ),
                reply_markup=get_post_registration_keyboard(language)
            )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=translations[language]['db_error']
            )
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao processar método de pagamento: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=translations[language]['db_error']
        )
        context.user_data.clear()

async def handle_card_selection(update: Update, context: CallbackContext):
    """Processa a seleção de cartão para pagamento"""
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    language = context.user_data.get('language', 'pt')
    card_id = query.data.split('_')[2]  # Extrai o ID do cartão do callback_data
    
    try:
        # Log para debug
        print(f"Card ID selecionado: {card_id}")
        
        # Recupera todos os dados do contexto
        user_data = context.user_data
        
        # Adiciona informação do cartão específico
        payment_method = f"card_{card_id}"
        
        success = insert_expense(
            user_id=query.message.chat_id,
            amount=user_data['amount'],
            category=user_data['category'],
            description=user_data.get('description', ""),
            payment_method=payment_method
        )
        
        if success:
            # Busca o cartão selecionado para exibição
            user_cards = get_user_cards(query.message.chat_id)
            print(f"Cartões disponíveis: {user_cards}")
            
            selected_card = None
            for card in user_cards:
                print(f"Verificando cartão: {card}")
                if str(card['card_id']) == card_id:
                    selected_card = card
                    break
            
            print(f"Cartão selecionado: {selected_card}")
            
            card_display = f"{selected_card['nickname']} (···{selected_card['last_four']})" if selected_card else "Cartão"
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=translations[language].get('saved_expense_card', "💰 Despesa de R${amount:.2f} registrada!\n📊 Categoria: {category}\n💳 Pagamento: {card_display}").format(
                    amount=user_data['amount'],
                    category=user_data['category'].replace('CATEGORY_', ''),
                    card_display=card_display
                ),
                reply_markup=get_post_registration_keyboard(language)
            )
        else:
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=translations[language]['db_error']
            )
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Erro ao processar seleção de cartão: {str(e)}")
        print(f"Detalhes do erro: {error_details}")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=translations[language]['db_error']
        )
    
    context.user_data.clear()  # Limpa todos os dados

async def handle_cancel_payment(update: Update, context: CallbackContext):
    """Cancela o fluxo de pagamento atual"""
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    language = context.user_data.get('language', 'pt')
    
    # Limpa os dados e volta ao menu principal
    context.user_data.clear()
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=translations[language].get('payment_canceled', "Operação cancelada."),
        reply_markup=get_main_keyboard(language)
    )

async def handle_change_payment_method(update: Update, context: CallbackContext):
    """Permite ao usuário escolher outro método de pagamento"""
    query = update.callback_query
    await query.answer()
    await query.message.delete()
    
    language = context.user_data.get('language', 'pt')
    
    # Mantém os dados do contexto e volta para seleção de método de pagamento
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=translations[language]['select_payment_method'],
        reply_markup=get_payment_method_keyboard(language)
    )