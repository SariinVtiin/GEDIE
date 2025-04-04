from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import timedelta, datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.permanent_session_lifetime = timedelta(minutes=30)

# Configurações da aplicação
app_config = {
    'app_name': 'Sistema de Login',
    'logo_path': 'img/logo.png',           # Logo principal para telas de login/cadastro
    'logo_small_path': 'img/logo-small.png', # Logo menor para o dashboard
    'company_name': 'Sua Empresa'          # Nome da empresa para título e copyright
}

# Simulação de banco de dados (em produção, use um banco de dados real)
users = {
    'admin@example.com': {
        'password': generate_password_hash('admin123'),
        'name': 'Administrador'
    }
}

# Dicionário para armazenar tentativas de login
login_attempts = {}
# Número máximo de tentativas permitidas
MAX_ATTEMPTS = 5
# Tempo de bloqueio em segundos
LOCKOUT_TIME = 15 * 60  # 15 minutos

# Função para verificar tentativas de login
def check_login_attempts(ip_address):
    current_time = datetime.now()
    
    # Se o IP não está no registro, adiciona-o
    if ip_address not in login_attempts:
        login_attempts[ip_address] = {
            'attempts': 0,
            'last_attempt': current_time,
            'locked_until': None
        }
        return True
    
    # Verifica se o usuário está bloqueado
    if login_attempts[ip_address]['locked_until'] is not None:
        if current_time < login_attempts[ip_address]['locked_until']:
            # Calcula tempo restante em minutos
            remaining = (login_attempts[ip_address]['locked_until'] - current_time).seconds // 60
            flash(f'Muitas tentativas de login. Tente novamente em {remaining} minutos.', 'error')
            return False
        else:
            # Desbloqueia se o tempo de bloqueio já passou
            login_attempts[ip_address]['locked_until'] = None
            login_attempts[ip_address]['attempts'] = 0
    
    return True

# Função para registrar uma tentativa falha
def record_failed_attempt(ip_address):
    current_time = datetime.now()
    
    # Incrementa o contador de tentativas
    login_attempts[ip_address]['attempts'] += 1
    login_attempts[ip_address]['last_attempt'] = current_time
    
    # Verifica se excedeu o número máximo de tentativas
    if login_attempts[ip_address]['attempts'] >= MAX_ATTEMPTS:
        login_attempts[ip_address]['locked_until'] = current_time + timedelta(seconds=LOCKOUT_TIME)
        return False
    
    # Mostra quantas tentativas restam
    attempts_left = MAX_ATTEMPTS - login_attempts[ip_address]['attempts']
    flash(f'Email ou senha inválidos! Tentativas restantes: {attempts_left}', 'error')
    return True

# Função para resetar as tentativas após login bem-sucedido
def reset_attempts(ip_address):
    if ip_address in login_attempts:
        login_attempts[ip_address]['attempts'] = 0
        login_attempts[ip_address]['locked_until'] = None

@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Obtém o IP do cliente (em produção, considere usar X-Forwarded-For se atrás de proxy)
        client_ip = request.remote_addr
        
        # Verifica se o IP não está bloqueado
        if not check_login_attempts(client_ip):
            return render_template('login.html', config=app_config)
        
        if email in users and check_password_hash(users[email]['password'], password):
            session.permanent = remember
            session['user'] = email
            
            # Reset das tentativas após login bem-sucedido
            reset_attempts(client_ip)
            
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Registra tentativa falha
            record_failed_attempt(client_ip)
    
    return render_template('login.html', config=app_config)

@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('Você foi desconectado!', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Por favor, faça login para acessar esta página!', 'warning')
        return redirect(url_for('login'))
    
    user_info = users[session['user']]
    return render_template('dashboard.html', user=user_info, config=app_config)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        name = request.form.get('name')
        
        if email in users:
            flash('Este email já está cadastrado!', 'error')
        elif password != confirm_password:
            flash('As senhas não coincidem!', 'error')
        else:
            users[email] = {
                'password': generate_password_hash(password),
                'name': name
            }
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('login'))
    
    return render_template('signup.html', config=app_config)

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        if email in users:
            # Em um sistema real, envie um email com link para redefinição
            flash('Instruções para redefinir sua senha foram enviadas para o seu email!', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email não encontrado!', 'error')
    
    return render_template('reset_password.html', config=app_config)

# Adicionar uma rota para verificar o status do bloqueio (útil para debugging)
@app.route('/check-lockout')
def check_lockout():
    if not app.debug:
        return "Esta página só está disponível no modo de desenvolvimento", 403
    
    client_ip = request.remote_addr
    if client_ip in login_attempts and login_attempts[client_ip]['locked_until']:
        remaining = (login_attempts[client_ip]['locked_until'] - datetime.now()).seconds // 60
        return f"IP {client_ip} está bloqueado por mais {remaining} minutos."
    return f"IP {client_ip} não está bloqueado."

if __name__ == '__main__':
    app.run(debug=True)