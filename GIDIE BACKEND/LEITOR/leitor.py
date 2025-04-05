from PIL import Image
import google.generativeai as genai
import os
import sys
import io

# Corrige encoding do terminal Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

genai.configure(api_key="AIzaSyAsx3NoyB2_IMQoqGGijSm83Q6vRkB64Mw")

def extrair_valor_total_imagem(nome_arquivo):
    try:
        caminho_absoluto = os.path.abspath(nome_arquivo)
        
        if not os.path.exists(caminho_absoluto):
            return "❌ Arquivo não encontrado"
            
        img = Image.open(caminho_absoluto)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """Analise e retorne APENAS o valor total no formato R$X.XX"""
        
        response = model.generate_content([prompt, img])
        return f"✅ {response.text.strip()}"
    
    except Exception as e:
        return f"⚠️ Erro: {str(e)}"

# Teste
resultado = extrair_valor_total_imagem(r"C:\Users\xvito\OneDrive\Área de Trabalho\GEDIE\GEDIE\GIDIE BACKEND\LEITOR\cupom.jpg")
print(resultado)