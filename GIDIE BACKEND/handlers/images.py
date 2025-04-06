from telegram import Update
from telegram.ext import CallbackContext, MessageHandler, filters
from config.languages import translations
from keyboards.inline import get_main_keyboard
import os
import uuid
from datetime import datetime
from services.ocr_processor import process_receipt
from database.db import insert_expense 

async def handle_send_image(update: Update, context: CallbackContext):
    """
    Inicia o processo de envio de imagem.
    
    Args:
        update: Objeto Update do Telegram
        context: Contexto da callback
    """
    query = update.callback_query
    await query.answer()
    language = context.user_data.get('language', 'pt')
    
    # Envia mensagem solicitando a imagem
    await query.message.reply_text(translations[language]['image_prompt'])
    await query.message.delete()

async def receive_image(update: Update, context: CallbackContext):
    """
    Recebe, salva e processa a imagem de um recibo enviada pelo usuário.
    
    Args:
        update: Objeto Update do Telegram
        context: Contexto da callback
    """
    language = context.user_data.get('language', 'pt')
    user_id = update.message.chat_id
    
    # Verifica se a mensagem contém uma foto
    if not update.message.photo:
        await update.message.reply_text(translations[language]['image_error'])
        
        # Volta ao menu principal
        await update.message.reply_text(
            translations[language]['back_to_main'],
            reply_markup=get_main_keyboard(language)
        )
        return
        
    try:
        # Gera nome único para o arquivo com ID do usuário
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = uuid.uuid4().hex[:6].upper()
        filename = f"user_{user_id}_{timestamp}_{unique_id}.jpg"
        file_path = os.path.join("receipts", filename)
        
        # Baixa e salva a imagem
        photo = update.message.photo[-1]  # Pega a maior resolução disponível
        file = await photo.get_file()
        await file.download_to_drive(file_path)
        
        # Notifica que a imagem foi recebida com sucesso
        await update.message.reply_text(translations[language]['image_success'])

        # Processa a imagem para extrair informações do recibo
        result = process_receipt(file_path)
        
        # Verifica se o processamento foi bem-sucedido (começa com ✅)
        if result.startswith("✅"):
            # Exibe mensagem de sucesso para o usuário
            await update.message.reply_text(
                translations[language].get('expense_added', 'Despesa adicionada com sucesso!')
            )
        else:
            # Exibe mensagem de erro para o usuário
            await update.message.reply_text(
                translations[language].get('ocr_error', 'Não foi possível processar o recibo.')
            )
            
    except Exception as e:
        # Tratamento para erros na manipulação do arquivo ou comunicação com Telegram
        print(f"Erro ao processar imagem: {str(e)}")
        await update.message.reply_text("🔧 Erro técnico. Tente novamente.")
    
    # Volta ao menu principal após completar processamento
    await update.message.reply_text(
        translations[language]['back_to_main'],
        reply_markup=get_main_keyboard(language)
    )