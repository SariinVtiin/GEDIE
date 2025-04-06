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
                description VARCHAR(255),
                payment_method VARCHAR(20) NOT NULL,  -- Vírgula correta e sem comentário inline
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                first_name VARCHAR(255),
                username VARCHAR(255),
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_cards (
                card_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT,
                last_four VARCHAR(4) NOT NULL,
                nickname VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        print("[DB] Tabela recriada com sucesso!")
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"[ERRO DB] Falha ao recriar tabela: {str(e)}")
        raise

def insert_expense(user_id, amount, category, payment_method ,description=""):
    try:
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO expenses 
            (user_id, amount, category, description, payment_method) 
            VALUES (%s, %s, %s, %s, %s)""",
            (user_id, float(amount), category, description, payment_method)
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

def register_user(user_id: int, first_name: str, username: str):
    """Registra usuário na primeira interação"""
    try:
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO users (user_id, first_name, username)
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE
               first_name = VALUES(first_name),
               username = VALUES(username)""",
            (user_id, first_name, username)
        )
        
        conn.commit()
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao registrar usuário: {str(e)}")
        return False

def get_user_cards(user_id: int):
    """Retorna todos os cartões do usuário"""
    try:
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT card_id, last_four, nickname FROM credit_cards WHERE user_id = %s",
            (user_id,)
        )
        return cursor.fetchall()
        
    except Exception as e:
        print(f"[ERRO] Falha ao buscar cartões: {str(e)}")
        return []
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def add_credit_card(user_id: int, last_four: str, nickname: str = None) -> bool:
    """Adiciona cartão de crédito ao banco de dados"""
    conn = None
    cursor = None
    
    try:
        # Validação básica do cartão
        if len(last_four) != 4 or not last_four.isdigit():
            print("[ERRO] Número do cartão inválido")
            return False
            
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()

        # Verifica se o usuário existe
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            print(f"[ERRO] Usuário {user_id} não registrado")
            return False

        # Insere o cartão
        cursor.execute(
            """INSERT INTO credit_cards (user_id, last_four, nickname)
               VALUES (%s, %s, %s)""",
            (user_id, last_four, nickname)
        )
        
        conn.commit()
        print(f"[DB] Cartão {last_four} cadastrado para o usuário {user_id}")
        return True
        
    except mysql.connector.Error as err:
        # Trata especificamente erros de foreign key
        if err.errno == 1452:
            print(f"[ERRO DB] Chave estrangeira inválida: {err.msg}")
        else:
            print(f"[ERRO DB] Código: {err.errno} | Mensagem: {err.msg}")
        return False
        
    except Exception as e:
        print(f"[ERRO] Falha inesperada: {str(e)}")
        return False
        
    finally:
        # Fecha conexões de forma segura
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()