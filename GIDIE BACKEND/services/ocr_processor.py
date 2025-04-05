import os
import re
import google.generativeai as genai
from PIL import Image
from database.db import insert_expense

genai.configure(api_key="AIzaSyAsx3NoyB2_IMQoqGGijSm83Q6vRkB64Mw")

def process_receipt(image_path: str) -> str:
    """Processa imagem de recibo e salva no banco"""
    try:
        # Extrair user_id do nome do arquivo
        filename = os.path.basename(image_path)
        match = re.search(r'user_(\d+)_', filename)
        
        if not match:
            return "❌ Formato de nome de arquivo inválido"
            
        user_id = int(match.group(1))
        
        # Processar imagem
        img = Image.open(image_path)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([
            "Extraia APENAS o valor total no formato numérico (ex: 50.99)",
            img
        ])
        
        # Converter para float
        total = float(response.text.strip().replace(",", "."))
        
        # Salvar no banco
        insert_expense(
            user_id=user_id,
            amount=total,
            category="AUTO_RECOGNITION",
            description=f"Registro automático - {os.path.basename(image_path)}"
        )
        
        return f"✅ Valor R${total:.2f} registrado automaticamente!"
        
    except Exception as e:
        return f"⚠️ Erro: {str(e)}"