# database/db.py
import mysql.connector
from config.config import Config

def create_table():
    """Cria ou recria a tabela do zero com todas as colunas necessárias"""
    try:
        print("[DB] Recriando tabela 'expenses'...")
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()

        # Remove a tabela se já existir
        cursor.execute("DROP TABLE IF EXISTS expenses")
        
        # Cria a nova tabela com estrutura completa
        cursor.execute("""
            CREATE TABLE expenses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                category VARCHAR(50) NOT NULL,
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

def insert_expense(user_id, amount, category):
    """Insere despesa no banco de dados"""
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO expenses (user_id, amount, category) VALUES (%s, %s, %s)",
            (user_id, float(amount), category)
        )
        conn.commit()
        print(f"[DB] Inserção bem-sucedida! ID: {cursor.lastrowid}")
        return True
        
    except mysql.connector.Error as err:
        print(f"[ERRO DB] Código: {err.errno} | Mensagem: {err.msg}")
        return False
    except Exception as e:
        print(f"[ERRO] Geral: {str(e)}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()