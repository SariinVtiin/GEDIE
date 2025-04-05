from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from config.languages import translations
from keyboards.inline import get_main_keyboard
import os
import uuid
from datetime import datetime
import threading
from services.ocr_processor import process_receipt

async def handle_send_image(update: Update, context: CallbackContext):  # <--- ADICIONE ESTA FUNÇÃO
    """Inicia o processo de envio de imagem"""
    query = update.callback_query
    await query.answer()
    language = context.user_data.get('language', 'pt')
    
    await query.message.reply_text(translations[language]['image_prompt'])
    await query.message.delete()

async def receive_image(update: Update, context: CallbackContext):
    """Salva imagem na pasta sem registrar no BD"""
    language = context.user_data.get('language', 'pt')
    user_id = update.message.chat_id
    
    try:
        if update.message.photo:
            # Gera nome único com ID do usuário
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_id = uuid.uuid4().hex[:6].upper()
            filename = f"user_{user_id}_{timestamp}_{unique_id}.jpg"
            file_path = os.path.join("receipts", filename)
            
            # Baixa e salva a imagem
            photo = update.message.photo[-1]
            file = await photo.get_file()
            await file.download_to_drive(file_path)
            
            await update.message.reply_text(translations[language]['image_success'])

            threading.Thread(
                target=process_receipt,
                args=(file_path,)
            ).start()

        else:
            await update.message.reply_text(translations[language]['image_error'])
    
    except Exception as e:
        await update.message.reply_text("🔧 Erro técnico. Tente novamente.")
    
    # Volta ao menu principal
    await update.message.reply_text(
        translations[language]['back_to_main'],
        reply_markup=get_main_keyboard(language)
    )