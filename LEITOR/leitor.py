import cv2
import pytesseract
import re
import os
import numpy as np
from pathlib import Path

# Configurar o caminho do Tesseract (AJUSTE ESTE CAMINHO!)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Configurações (Altere conforme necessário)
PASTA_IMAGENS = 'receipts'
NOME_ARQUIVO = 'exemplo.jpg'  # Coloque o nome exato do seu arquivo
MODO_DEBUG = True  # Mostra detalhes do processamento

def verificar_estrutura():
    """Resolve problemas de caminho e codificação"""
    try:
        # Converter caminho para raw string
        dir_base = Path(__file__).parent.resolve()
        dir_base = Path(str(dir_base).encode('utf-8').decode('utf-8'))
        
        pasta_imagens = dir_base / PASTA_IMAGENS
        pasta_imagens.mkdir(exist_ok=True, parents=True)
        
        return pasta_imagens
        
    except Exception as e:
        print(f"Erro na estrutura: {str(e)}")
        return None

def preprocessar_imagem(img):
    """Melhora a qualidade da imagem para OCR"""
    try:
        # Converter para escala de cinza
        cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Redimensionar
        cinza = cv2.resize(cinza, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
        
        # Remover ruído
        cinza = cv2.medianBlur(cinza, 3)
        
        # Binarização adaptativa
        limiar = cv2.adaptiveThreshold(cinza, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                     cv2.THRESH_BINARY, 11, 2)
        
        # Melhorar contraste
        kernel = np.ones((1, 1), np.uint8)
        limiar = cv2.dilate(limiar, kernel, iterations=1)
        limiar = cv2.erode(limiar, kernel, iterations=1)
        
        return limiar
        
    except Exception as e:
        print(f"Erro no pré-processamento: {str(e)}")
        return None

def carregar_imagem(caminho):
    """Carrega imagem com tratamento de erros"""
    try:
        # Verificar permissões e integridade do arquivo
        if not caminho.is_file():
            print(f"Arquivo não encontrado: {caminho}")
            return None
            
        # Tentar abrir em modo binário para verificar corrupção
        with open(caminho, 'rb') as f:
            if not f.read():
                print("Arquivo vazio/corrompido")
                return None
                
        # Ler com OpenCV usando caminho absoluto
        img = cv2.imread(str(caminho.resolve()))
        if img is None:
            print("OpenCV não suporta este formato de arquivo")
            return None
            
        return img
        
    except Exception as e:
        print(f"Erro ao carregar: {str(e)}")
        return None

def extrair_total(caminho_imagem):
    """Função principal para extrair o valor total"""
    try:
        # Verificar se o arquivo existe
        if not caminho_imagem.exists():
            print(f"Arquivo não encontrado: {caminho_imagem}")
            return None
            
        # Ler imagem
        img = cv2.imread(str(caminho_imagem))
        if img is None:
            print(f"Erro ao ler imagem: {caminho_imagem}")
            return None
            
        # Pré-processamento
        img_processada = preprocessar_imagem(img)
        if img_processada is None:
            return None
            
        # Configurar parâmetros do Tesseract
        config = r'--oem 3 --psm 6 -l por+eng'
        texto = pytesseract.image_to_string(img_processada, config=config)
        
        if MODO_DEBUG:
            print("\nTexto extraído:\n", texto)
            cv2.imshow('Imagem Processada', img_processada)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        # Padrões regex melhorados
        padroes = [
            r'(?i)(?:total|valor\s+total|total\s+a\s+pagar)[\s:\-]*R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})',
            r'(?i)R?\$?\s*(\d{1,3}(?:\.\d{3})*,\d{2})(?=\s*?total)',
            r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*$'
        ]
        
        candidatos = []
        for padrao in padroes:
            matches = re.findall(padrao, texto)
            if matches:
                for match in matches:
                    try:
                        valor = float(match.replace('.', '').replace(',', '.'))
                        candidatos.append(valor)
                    except:
                        continue
        
        # Selecionar o maior valor único
        if candidatos:
            valores_unicos = sorted(list(set(candidatos)), reverse=True)
            return valores_unicos[0]
            
        return None

    except Exception as e:
        print(f"Erro durante processamento: {str(e)}")
        return None

def main():
    # Verificar estrutura
    pasta_imagens = verificar_estrutura()
    if not pasta_imagens:
        return
    
    # Caminho seguro com raw string
    caminho_imagem = pasta_imagens / NOME_ARQUIVO
    caminho_imagem = Path(str(caminho_imagem).encode('utf-8').decode('utf-8'))
    
    print("\n" + "="*60)
    print(f"Verificando acesso ao arquivo:")
    print(f"Caminho RAW: {r'%s' % caminho_imagem}")
    print(f"Existe: {'Sim' if caminho_imagem.exists() else 'Não'}")
    print(f"Tamanho: {caminho_imagem.stat().st_size if caminho_imagem.exists() else 0} bytes")
    print("="*60 + "\n")
    
    # Carregar imagem
    img = carregar_imagem(caminho_imagem)
    if img is None:
        print("Falha crítica - verifique:")
        print(f"1. O arquivo está na pasta: {pasta_imagens}?")
        print(f"2. Nome exato: '{NOME_ARQUIVO}' (case sensitive)")
        print(f"3. Formato suportado (JPG/PNG/BMP)")
        print(f"4. Permissões de leitura do arquivo")
        return
        
    # Processar imagem
    total = extrair_total(caminho_imagem)
    
    # Resultado
    if total:
        print(f"\n[SUCESSO] Valor total encontrado: R$ {total:.2f}")
    else:
        print("\n[FALHA] Não foi possível identificar o valor total. Verifique:")
        print("- A qualidade da imagem (deve estar legível)")
        print("- O valor está visível e bem posicionado")
        print("- Tente ativar o MODO_DEBUG para análise")

if __name__ == "__main__":
    main()