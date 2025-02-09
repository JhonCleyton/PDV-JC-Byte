from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, login_required
from flask_migrate import Migrate
from models import db, User, CompanyInfo
from routes.auth import auth_bp
from routes.categories import categories_bp
from routes.customers import customers_bp
from routes.suppliers import suppliers_bp
from routes.products import products_bp
from routes.vendas import vendas_bp
from routes.contas_a_receber import contas_a_receber_bp
from routes.contas_a_pagar import contas_a_pagar_bp
from routes.nf import nf_bp
from routes.notifications import notifications_bp
from routes.dashboard import dashboard_bp
from routes.users import users_bp
from routes.clientes import clientes_bp
from routes.settings import settings_bp
from routes.management import management
from datetime import timedelta
from werkzeug.security import generate_password_hash
from notifications_manager import check_notifications
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Configurações
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Altere para uma chave secreta segura
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)  # Sessão expira em 8 horas

# Inicialização do banco de dados
db.init_app(app)
migrate = Migrate(app, db)

# Configuração do Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Registro dos blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(products_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(suppliers_bp)
app.register_blueprint(customers_bp)
app.register_blueprint(vendas_bp)
app.register_blueprint(contas_a_receber_bp)
app.register_blueprint(contas_a_pagar_bp)
app.register_blueprint(nf_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(dashboard_bp, url_prefix='/management')
app.register_blueprint(clientes_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(management, url_prefix='/management')

@app.before_request
def before_request():
    """Executa antes de cada requisição"""
    if not request.path.startswith('/static/'):  # Ignora arquivos estáticos
        check_notifications()

def init_admin():
    """Cria um usuário administrador se não existir"""
    with app.app_context():
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                name='Administrador',
                username='admin',
                password=generate_password_hash('admin'),
                role='admin',
                status='active'
            )
            db.session.add(admin)
            db.session.commit()
            print('Usuário admin criado com sucesso!')

def init_company_info():
    """Cria a tabela e registro inicial de company_info"""
    with app.app_context():
        # Verifica se já existe um registro
        company = CompanyInfo.query.first()
        if not company:
            # Cria um registro inicial
            company = CompanyInfo(
                name='',
                cnpj='',
                ie='',
                address='',
                city='',
                state='',
                zip_code='',
                phone='',
                email='',
                printer_name='',
                print_header='',
                print_footer='',
                auto_print=True
            )
            db.session.add(company)
            db.session.commit()
            print('Registro inicial de company_info criado')

# Rotas principais
@app.route('/')
@login_required
def index():
    """Redireciona para o PDV"""
    return redirect(url_for('vendas.create'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/products')
@login_required
def products():
    return render_template('products.html')

@app.route('/categories')
@login_required
def categories():
    return render_template('categories.html')

@app.route('/suppliers')
@login_required
def suppliers():
    return render_template('suppliers.html')

@app.route('/customers')
@login_required
def customers():
    return render_template('customers.html')

@app.route('/sales')
@login_required
def sales():
    return redirect(url_for('vendas.list_sales'))

@app.route('/invoices')
@login_required
def invoices():
    return render_template('invoices/list.html')

@app.route('/invoices/manage')
@login_required
def manage_invoice():
    return render_template('invoices/manage.html')

@app.route('/receivables')
@login_required
def receivables():
    return render_template('receivables.html')

@app.route('/payables')
@login_required
def payables():
    return render_template('payables.html')

if __name__ == '__main__':
    with app.app_context():
        # Primeiro cria todas as tabelas
        print('Criando tabelas...')
        db.create_all()
        
        # Depois inicializa os dados
        print('Inicializando dados...')
        init_admin()
        init_company_info()
    
    # Obtém o endereço IP da máquina
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print(f'\nServidor iniciado!')
    print(f'Acesse o sistema através dos seguintes endereços:')
    print(f'- Local: http://localhost:5000')
    print(f'- Rede: http://{local_ip}:5000')
    
    # Inicia o servidor permitindo acesso externo
    app.run(host='0.0.0.0', port=5000, debug=True)
