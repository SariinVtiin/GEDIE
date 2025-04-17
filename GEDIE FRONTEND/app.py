from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import bcrypt
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuração do banco de dados a partir do arquivo de configuração
DB_CONFIG = {
    'host': 'maglev.proxy.rlwy.net',
    'user': 'root',
    'password': 'JaZeyqeyVUiucaTBBdtvdehXNNprhhSv',
    'database': 'railway',
    'port': 10053
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

def setup_database():
    """Configurar banco de dados com novos campos necessários"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se os novos campos já existem
        cursor.execute("SHOW COLUMNS FROM users LIKE 'email'")
        email_exists = cursor.fetchone()
        
        if not email_exists:
            cursor.execute("""
                ALTER TABLE users 
                ADD COLUMN full_name VARCHAR(255),
                ADD COLUMN email VARCHAR(255) UNIQUE,
                ADD COLUMN cpf VARCHAR(14) UNIQUE,
                ADD COLUMN birth_date DATE,
                ADD COLUMN password_hash VARCHAR(255),
                ADD COLUMN is_registered BOOLEAN DEFAULT FALSE
            """)
            print("Tabela users atualizada com sucesso!")
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Erro ao configurar banco de dados: {str(e)}")

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    login_type = request.form.get('login_type')
    
    if login_type == 'first_access':
        user_id = request.form.get('user_id')
        access_code = request.form.get('access_code')
        
        if not user_id or not access_code:
            flash('Por favor, preencha todos os campos', 'error')
            return redirect(url_for('index'))
        
        try:
            # Converte user_id para inteiro (o Telegram usa IDs numéricos)
            user_id = int(user_id)
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Verifica se o usuário existe e o código corresponde
            cursor.execute(
                "SELECT * FROM users WHERE user_id = %s AND access_code = %s",
                (user_id, access_code)
            )
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not user:
                flash('ID de usuário ou código de acesso inválido', 'error')
                return redirect(url_for('index'))
            
            # Verifica se o usuário já completou o cadastro
            if user.get('is_registered'):
                flash('Este usuário já completou o cadastro. Por favor, faça login com email e senha', 'error')
                return redirect(url_for('index'))
            
            # Armazenar dados do usuário para o registro
            session['user_id'] = user_id
            session['first_name'] = user.get('first_name', '')
            
            return redirect(url_for('register'))
            
        except ValueError:
            flash('ID de usuário deve ser um número', 'error')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Erro ao tentar login: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    elif login_type == 'regular':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Por favor, preencha todos os campos', 'error')
            return redirect(url_for('index'))
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Busca o usuário pelo email e verifica se está registrado
            cursor.execute(
                "SELECT * FROM users WHERE email = %s AND is_registered = TRUE",
                (email,)
            )
            user = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if not user:
                flash('Email ou senha inválidos', 'error')
                return redirect(url_for('index'))
            
            # Verifica a senha usando bcrypt
            if not bcrypt.checkpw(password.encode('utf-8'), user.get('password_hash', '').encode('utf-8')):
                flash('Email ou senha inválidos', 'error')
                return redirect(url_for('index'))
            
            # Autenticar usuário
            session['user_id'] = user.get('user_id')
            session['full_name'] = user.get('full_name')
            session['is_authenticated'] = True
            
            # Redirecionar para dashboard (que será implementado no futuro)
            return render_template('success.html', message="Login realizado com sucesso! Bem-vindo ao GEDIE.")
            
        except Exception as e:
            flash(f'Erro ao tentar login: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    flash('Tipo de login inválido', 'error')
    return redirect(url_for('index'))

@app.route('/register')
def register():
    # Verificar se o usuário está no processo de primeiro acesso
    if 'user_id' not in session:
        flash('Acesso negado', 'error')
        return redirect(url_for('index'))
    
    return render_template('register.html', first_name=session.get('first_name', ''))

@app.route('/complete_registration', methods=['POST'])
def complete_registration():
    # Verificar se o usuário está no processo de primeiro acesso
    if 'user_id' not in session:
        flash('Acesso negado', 'error')
        return redirect(url_for('index'))
    
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    cpf = request.form.get('cpf')
    birth_date = request.form.get('birth_date')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    
    # Validações básicas
    if not all([full_name, email, cpf, birth_date, password, confirm_password]):
        flash('Por favor, preencha todos os campos', 'error')
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash('As senhas não coincidem', 'error')
        return redirect(url_for('register'))
    
    try:
        # Formatar o CPF para armazenamento (remover formatação)
        cpf = cpf.replace('.', '').replace('-', '')
        
        # Gerar hash da senha
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Formatar data de nascimento para o MySQL (YYYY-MM-DD)
        formatted_birth_date = datetime.strptime(birth_date, '%Y-%m-%d').strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Atualizar informações do usuário
        cursor.execute("""
            UPDATE users
            SET full_name = %s, email = %s, cpf = %s, birth_date = %s, 
                password_hash = %s, is_registered = TRUE
            WHERE user_id = %s
        """, (full_name, email, cpf, formatted_birth_date, password_hash, session['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Limpar dados de registro da sessão e configurar autenticação
        user_id = session.pop('user_id', None)
        session.pop('first_name', None)
        
        session['user_id'] = user_id
        session['full_name'] = full_name
        session['is_authenticated'] = True
        
        flash('Registro concluído com sucesso!', 'success')
        return render_template('success.html', message="Cadastro realizado com sucesso! Bem-vindo ao GEDIE.")
        
    except mysql.connector.Error as e:
        # Tratar erros específicos do MySQL
        if e.errno == 1062:  # Violação de chave única
            if "email" in str(e):
                flash('Este email já está em uso', 'error')
            elif "cpf" in str(e):
                flash('Este CPF já está cadastrado', 'error')
            else:
                flash('Erro de duplicidade no cadastro', 'error')
        else:
            flash(f'Erro no banco de dados: {str(e)}', 'error')
        return redirect(url_for('register'))
    except Exception as e:
        flash(f'Erro ao completar registro: {str(e)}', 'error')
        return redirect(url_for('register'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/how-to-register')
def how_to_register():
    return render_template('how_to_register.html')

@app.route('/reset-password', methods=['POST'])
def reset_password():
    email = request.form.get('email')
    
    if not email:
        flash('Por favor, informe o e-mail cadastrado', 'error')
        return redirect(url_for('forgot_password'))
    
    try:
        # Verificar se o e-mail existe
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT user_id, first_name FROM users WHERE email = %s AND is_registered = TRUE",
            (email,)
        )
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not user:
            # Por segurança, não informamos que o e-mail não existe
            flash('Se o e-mail estiver cadastrado, você receberá as instruções de recuperação', 'success')
            return redirect(url_for('index'))
        
        # Aqui você implementaria o envio real de e-mail
        # Como é uma simulação, apenas mostramos uma mensagem de sucesso
        
        flash('Instruções de recuperação de senha enviadas para seu e-mail', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash('Ocorreu um erro ao processar sua solicitação', 'error')
        return redirect(url_for('forgot_password'))

@app.route('/dashboard')
def dashboard():
    # Verificar se o usuário está autenticado
    if 'is_authenticated' not in session or not session['is_authenticated']:
        flash('Você precisa fazer login primeiro', 'error')
        return redirect(url_for('index'))
    
    # Obter dados do usuário da sessão
    user_id = session.get('user_id')
    full_name = session.get('full_name', 'Usuário')
    
    try:
        # Conectar ao banco de dados
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Buscar resumo de despesas por categoria
        cursor.execute("""
            SELECT 
                category, 
                SUM(amount) as total 
            FROM expenses 
            WHERE user_id = %s
            GROUP BY category 
            ORDER BY total DESC
        """, (user_id,))
        
        categories = cursor.fetchall()
        
        # Buscar despesas recentes (últimas 5)
        cursor.execute("""
            SELECT 
                id, 
                amount, 
                category, 
                description, 
                payment_method,
                created_at
            FROM expenses 
            WHERE user_id = %s 
            ORDER BY created_at DESC 
            LIMIT 5
        """, (user_id,))
        
        recent_expenses = cursor.fetchall()
        
        # Calcular o total de despesas do mês atual
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        cursor.execute("""
            SELECT 
                SUM(amount) as monthly_total 
            FROM expenses 
            WHERE 
                user_id = %s AND 
                MONTH(created_at) = %s AND 
                YEAR(created_at) = %s
        """, (user_id, current_month, current_year))
        
        monthly_result = cursor.fetchone()
        monthly_total = monthly_result['monthly_total'] if monthly_result and monthly_result['monthly_total'] else 0
        
        # Buscar os cartões do usuário
        cursor.execute("""
            SELECT card_id, last_four, nickname 
            FROM credit_cards 
            WHERE user_id = %s
        """, (user_id,))
        
        cards = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Enviar dados para o template
        return render_template(
            'dashboard.html',
            full_name=full_name,
            categories=categories,
            recent_expenses=recent_expenses,
            monthly_total=monthly_total,
            cards=cards
        )
        
    except Exception as e:
        print(f"Erro ao carregar dashboard: {str(e)}")
        flash('Erro ao carregar os dados do dashboard', 'error')
        return redirect(url_for('index'))

@app.route('/success', methods=['GET'])
def success_page():
    message = request.args.get('message', 'Operação realizada com sucesso!')
    return render_template('success.html', message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)