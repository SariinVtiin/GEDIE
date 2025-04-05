# database/db.py
import mysql.connector
from config.config import Config

def create_table():
    """Cria ou recria a tabela do zero com todas as colunas necessárias"""
    try:
        print("[DB] Recriando tabela 'expenses'...")
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS expenses")
        
        cursor.execute("""
            CREATE TABLE expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                category VARCHAR(50) NOT NULL,
                description VARCHAR(255),  -- Nova coluna
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        print("[DB] Tabela recriada com sucesso!")
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERRO DB] Falha ao recriar tabela: {str(e)}")
        raise

def insert_expense(user_id, amount, category, description=""):
    try:
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category, description) VALUES (%s, %s, %s, %s)",
            (user_id, float(amount), category, description)  # Adicione o quarto parâmetro
        )
        
        conn.commit()
        print(f"[DB] Inserção bem-sucedida! ID: {cursor.lastrowid}")
        return True
        
    except mysql.connector.Error as err:
        print(f"[ERRO DB] Código: {err.errno} | Mensagem: {err.msg}")
        return False
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()