# database/db.py
import mysql.connector
from config.config import Config
from mysql.connector import Error
import random
import string

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
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT UNIQUE,
                first_name VARCHAR(255),
                last_name VARCHAR(255),
                username VARCHAR(255),
                language_code VARCHAR(10),
                is_bot BOOLEAN,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_code VARCHAR(6)
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

def generate_access_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

def register_user(user_id: int, first_name: str, username: str, last_name: str = None, language_code: str = None, is_bot: bool = False):
    """
    Registra ou atualiza o usuário com informações adicionais.
    
    Parâmetros:
      - user_id: ID único do usuário (do Telegram).
      - first_name: Primeiro nome do usuário.
      - username: Nome de usuário.
      - last_name: Sobrenome (opcional).
      - language_code: Código do idioma (opcional).
      - is_bot: Indica se é um bot (normalmente False para usuários humanos).
    """
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()
        
        access_code = generate_access_code()
        
        query = """
            INSERT INTO users (user_id, first_name, username, last_name, language_code, is_bot, access_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                first_name = VALUES(first_name),
                username = VALUES(username),
                last_name = VALUES(last_name),
                language_code = VALUES(language_code),
                is_bot = VALUES(is_bot),
                access_code = VALUES(access_code)
        """
        cursor.execute(query, (user_id, first_name, username, last_name, language_code, is_bot, access_code))
        conn.commit()
        return True
    except Error as e:
        print(f"[ERRO] Falha ao registrar usuário: {str(e)}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()

def get_user_code(user_id):
    try:
        conn = mysql.connector.connect(**Config.DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT access_code FROM users WHERE user_id = %s", (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"Erro ao buscar código do usuário: {str(e)}")
        return None

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