from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.languages import translations

def get_main_keyboard(language='pt'):
    keyboard = [
        [InlineKeyboardButton(translations[language]['enter_amount'], callback_data="enter_value")],
        [InlineKeyboardButton(translations[language]['settings'], callback_data="open_settings")],  # Novo
        [InlineKeyboardButton(translations[language]['send_image'], callback_data="send_image")],
        [InlineKeyboardButton(translations[language]['exit'], callback_data="exit")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard(language='pt'):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(translations[language]['change_language'], callback_data="change_language")],
        [InlineKeyboardButton(translations[language]['add_card'], callback_data="add_credit_card")],
        [InlineKeyboardButton(translations[language]['my_cards'], callback_data="list_cards")],
        [
            InlineKeyboardButton(translations[language]['back_to_main'], callback_data="back_to_main"),
            InlineKeyboardButton(translations[language]['back_to_settings'], callback_data="open_settings")
        ]
    ])

def get_categories_keyboard(language='pt'):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(translations[language]['groceries'], callback_data="CATEGORY_GROCERIES")],
        [InlineKeyboardButton(translations[language]['transport'], callback_data="CATEGORY_TRANSPORT")],
        [InlineKeyboardButton(translations[language]['leisure'], callback_data="CATEGORY_LEISURE")],
        [InlineKeyboardButton(translations[language]['food'], callback_data="CATEGORY_FOOD")],
        [InlineKeyboardButton(translations[language]['bills'], callback_data="CATEGORY_BILLS")],
        [InlineKeyboardButton(translations[language]['health'], callback_data="CATEGORY_HEALTH")],
        [InlineKeyboardButton(translations[language]['others'], callback_data="CATEGORY_OTHERS")]
    ])

def get_post_registration_keyboard(language='pt'):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(translations[language]['register_again'], callback_data="register_again")],
        [InlineKeyboardButton(translations[language]['back_to_main'], callback_data="back_to_main")]
    ])

def get_description_keyboard(language='pt'):
    """Teclado para etapa de descrição"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            translations[language]['skip_description'], 
            callback_data="skip_description"
        )]
    ])

def get_card_delete_keyboard(cards, language='pt'):
    buttons = [
        [InlineKeyboardButton(
            f"❌ {card['nickname']} (···{card['last_four']})", 
            callback_data=f"delete_card_{card['card_id']}"
        )] for card in cards
    ]
    buttons.append([InlineKeyboardButton(translations[language]['back'], callback_data="cancel_delete")])
    return InlineKeyboardMarkup(buttons)

def get_payment_method_keyboard(language: str = 'pt'):
    buttons = [
        [InlineKeyboardButton("💳 Cartão", callback_data="PAYMENT_card")],
        [InlineKeyboardButton("💵 Dinheiro", callback_data="PAYMENT_cash")],
        [InlineKeyboardButton("📱 Pix", callback_data="PAYMENT_pix")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_user_cards_keyboard(cards, language='pt'):
    """Cria um teclado com os cartões do usuário para seleção durante pagamento"""
    buttons = [
        [InlineKeyboardButton(
            f"{card['nickname']} (···{card['last_four']})", 
            callback_data=f"select_card_{card['card_id']}"
        )] for card in cards
    ]
    buttons.append([InlineKeyboardButton(
        translations[language].get('cancel', "Cancelar"), 
        callback_data="cancel_payment"
    )])
    return InlineKeyboardMarkup(buttons)

def get_card_registration_keyboard(language='pt'):
    """Cria um teclado para opções após informar que não há cartões"""
    buttons = [
        [InlineKeyboardButton(
            translations[language].get('add_card', "Adicionar Cartão"), 
            callback_data="add_credit_card"
        )],
        [InlineKeyboardButton(
            translations[language].get('change_payment', "Mudar Método de Pagamento"), 
            callback_data="change_payment_method"
        )],
        [InlineKeyboardButton(
            translations[language].get('cancel', "Cancelar"), 
            callback_data="cancel_payment"
        )]
    ]
    return InlineKeyboardMarkup(buttons)