from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config.languages import translations

# Teclado principal dinâmico
def get_main_keyboard(language='pt'):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(translations[language]['enter_amount'], callback_data="enter_value")],
        [InlineKeyboardButton(translations[language]['change_language'], callback_data="change_language")],
        [InlineKeyboardButton(translations[language]['send_image'], callback_data="send_image")],
        [InlineKeyboardButton(translations[language]['exit'], callback_data="exit")]
    ])

# Teclado de categorias traduzido
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

# Menu pós-registro traduzido
def get_post_registration_keyboard(language='pt'):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(translations[language]['register_again'], callback_data="register_again")],
        [InlineKeyboardButton(translations[language]['back_to_main'], callback_data="back_to_main")]
    ])