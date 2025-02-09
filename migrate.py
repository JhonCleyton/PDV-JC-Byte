from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import traceback
from flask_login import UserMixin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(UserMixin, db.Model):
    __tablename__ = 'system_users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='cashier')
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(14), unique=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(8))
    contact_name = db.Column(db.String(100))
    payment_terms = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    cost_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    markup = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    selling_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    stock = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=0)
    expiry_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    credit_limit = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    current_debt = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    supervisor_id = db.Column(db.Integer, db.ForeignKey('system_users.id'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    payment_method = db.Column(db.String(20))
    status = db.Column(db.String(20))

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    discount = db.Column(db.Numeric(10, 2), default=0)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    method = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20))

class Receivable(db.Model):
    __tablename__ = 'receivables'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'))
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20))
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Payable(db.Model):
    __tablename__ = 'payables'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20))
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reference_id = db.Column(db.Integer)
    reference_type = db.Column(db.String(50))

class CompanyInfo(db.Model):
    __tablename__ = 'company_info'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    cnpj = db.Column(db.String(14), unique=True)
    ie = db.Column(db.String(10))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(8))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    printer_name = db.Column(db.String(100))
    print_header = db.Column(db.String(200))
    print_footer = db.Column(db.String(200))
    auto_print = db.Column(db.Boolean, default=False)

def migrate():
    """Executa a migração do banco de dados"""
    try:
        # Remove o banco de dados existente
        if os.path.exists('pdv.db'):
            os.remove('pdv.db')
            print("Banco de dados existente removido.")
        
        # Cria as tabelas
        db.create_all()
        print("Tabelas criadas com sucesso.")
        
        # Cria o usuário admin
        admin = User(
            name='Administrador',
            username='admin',
            role='admin',
            status='active'
        )
        admin.set_password('admin')
        db.session.add(admin)
        
        # Cria as categorias básicas
        categories = [
            Category(name='Alimentos'),
            Category(name='Bebidas'),
            Category(name='Limpeza'),
            Category(name='Higiene'),
            Category(name='Outros')
        ]
        for category in categories:
            db.session.add(category)
        
        # Cria as configurações da empresa
        company = CompanyInfo(
            name='Minha Empresa',
            cnpj='00000000000000',
            ie='000000000',
            address='Rua Principal, 123',
            city='Cidade',
            state='UF',
            zip_code='00000000',
            phone='0000000000',
            email='empresa@email.com',
            printer_name='',
            print_header='CUPOM FISCAL\n{company_name}\nCNPJ: {cnpj}\nIE: {ie}\n{address}\n{city}-{state}',
            print_footer='Obrigado pela preferência!\nVolte sempre!\n{datetime}',
            auto_print=True
        )
        db.session.add(company)
        
        # Commit das alterações
        db.session.commit()
        print("Dados iniciais criados com sucesso.")
        
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        traceback.print_exc()
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        migrate()
