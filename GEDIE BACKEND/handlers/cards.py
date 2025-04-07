from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from database.db import add_credit_card, register_user
from keyboards.inline import get_main_keyboard
from config.languages import translations
from database.db import get_user_cards
from keyboards.inline import get_settings_keyboard

async def start_add_card(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    language = context.user_data.get('language', 'pt')
    
    # Define o estado de cadastro de cartão
    context.user_data['current_flow'] = 'card_registration'
    
    await query.message.reply_text(
        translations[language]['enter_card_details'],
        parse_mode="Markdown"
    )
    await query.message.delete()

async def handle_card_input(update: Update, context: CallbackContext):
    """Processa os dados do cartão"""
    if context.user_data.get('current_flow') != 'card_registration':
        return
    
    language = context.user_data.get('language', 'pt')
    user_input = update.message.text.strip()
    user = update.message.from_user

    try:
        # Validação básica
        if len(user_input) < 4 or not user_input[:4].isdigit():
            raise ValueError("Formato inválido")

        last_four = user_input[:4]
        nickname = user_input[4:].strip() or None

        # →→→ Registra o usuário ANTES do cartão ←←←
        register_user(
            user_id=user.id,
            first_name=user.first_name,
            username=user.username
        )

        # Tenta cadastrar o cartão
        success = add_credit_card(
            user_id=user.id,
            last_four=last_four,
            nickname=nickname
        )

        if success:
            confirmation = (
                f"✅ *Cartão cadastrado com sucesso!*\n\n"
                f"• Últimos dígitos: `•••• {last_four}`\n"
                f"• Apelido: {nickname if nickname else 'Não informado'}"
            )
            await update.message.reply_text(
                confirmation,
                parse_mode="Markdown",
                reply_markup=get_settings_keyboard(language)
            )
        else:
            await update.message.reply_text(
                translations[language]['card_error'],
                reply_markup=get_settings_keyboard(language)
            )
            
        context.user_data.pop('current_flow', None)

    except Exception as e:
        context.user_data.pop('current_flow', None)
        await update.message.reply_text(
            translations[language]['invalid_card_format'],
            reply_markup=get_settings_keyboard(language)
        )
    
    # →→→ Remove APENAS o estado do fluxo ←←←
    context.user_data.pop('current_flow', None)  # Redundância para garantir

async def list_cards(update: Update, context: CallbackContext):
    """Exibe todos os cartões do usuário"""
    query = update.callback_query
    await query.answer()
    language = context.user_data.get('language', 'pt')
    user_id = query.from_user.id
    
    try:
        # Busca cartões
        cards = get_user_cards(user_id)
        
        # Formata mensagem
        if not cards:
            message = translations[language]['no_cards']
        else:
            card_list = "\n".join([
                translations[language]['card_item'].format(
                    nickname=card['nickname'] or "Sem apelido",
                    last_four=card['last_four']
                ) for card in cards
            ])
            message = f"{translations[language]['your_cards']}\n\n{card_list}"
        
        # Envia resposta
        await query.message.edit_text(
            text=message,
            reply_markup=get_settings_keyboard(language)
        )
        
    except Exception as e:
        await query.message.reply_text("🔧 Erro técnico. Tente novamente mais tarde.")