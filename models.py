from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta, date
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal
import traceback

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modelo para usuários do sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120))
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, manager, seller
    status = db.Column(db.String(20), nullable=False)  # active, inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    sales_supervised = db.relationship('Sale', back_populates='supervisor', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'username': self.username,
            'email': self.email,
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
    
    # Relacionamentos
    parent = db.relationship('Category', remote_side=[id], back_populates='children')
    children = db.relationship('Category', back_populates='parent', remote_side=[parent_id])
    products = db.relationship('Product', back_populates='category', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

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
    
    # Relacionamentos
    products = db.relationship('Product', back_populates='supplier', lazy=True)
    payables = db.relationship('Payable', back_populates='supplier', lazy=True)
    invoices = db.relationship('Invoice', back_populates='supplier', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'cnpj': self.cnpj,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'contact_name': self.contact_name,
            'payment_terms': self.payment_terms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    cost_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    selling_price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    markup = db.Column(db.Numeric(10, 2), nullable=False, default=0)  # Percentual de markup
    min_stock = db.Column(db.Numeric(10, 3), default=0)
    max_stock = db.Column(db.Numeric(10, 3), default=0)
    stock = db.Column(db.Numeric(10, 3), nullable=False, default=0)
    unit = db.Column(db.String(10), default='un')  # un, kg, g, l, ml
    barcode = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')  # active, inactive
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    expiry_date = db.Column(db.Date, nullable=True)  # Data de validade
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    category = db.relationship('Category', back_populates='products', lazy=True)
    supplier = db.relationship('Supplier', back_populates='products', lazy=True)
    sale_items = db.relationship('SaleItem', back_populates='product', lazy=True)
    invoice_items = db.relationship('InvoiceItem', back_populates='product', lazy=True)
    
    def __init__(self, **kwargs):
        if 'cost_price' in kwargs:
            kwargs['cost_price'] = Decimal(str(kwargs['cost_price']))
        if 'selling_price' in kwargs:
            kwargs['selling_price'] = Decimal(str(kwargs['selling_price']))
        if 'markup' in kwargs:
            kwargs['markup'] = Decimal(str(kwargs['markup']))
        if 'min_stock' in kwargs:
            kwargs['min_stock'] = Decimal(str(kwargs['min_stock']))
        if 'max_stock' in kwargs:
            kwargs['max_stock'] = Decimal(str(kwargs['max_stock']))
        if 'stock' in kwargs:
            kwargs['stock'] = Decimal(str(kwargs['stock']))
        super(Product, self).__init__(**kwargs)
        
        # Calcula o preço de venda se não foi fornecido
        if not kwargs.get('selling_price') and kwargs.get('cost_price') and kwargs.get('markup'):
            self.update_selling_price()
    
    def update_selling_price(self):
        """Atualiza o preço de venda com base no custo e markup"""
        if self.cost_price:
            markup_decimal = (self.markup or Decimal('30')) / 100  # Usa 30% como markup padrão se não definido
            self.selling_price = self.cost_price * (1 + markup_decimal)
            self.selling_price = Decimal(str(self.selling_price)).quantize(Decimal('0.01'))
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'cost_price': float(self.cost_price) if self.cost_price else 0,
            'selling_price': float(self.selling_price) if self.selling_price else 0,
            'markup': float(self.markup) if self.markup else 0,
            'min_stock': float(self.min_stock) if self.min_stock else 0,
            'max_stock': float(self.max_stock) if self.max_stock else 0,
            'stock': float(self.stock) if self.stock else 0,
            'unit': self.unit,
            'barcode': self.barcode,
            'status': self.status,
            'category_id': self.category_id,
            'supplier_id': self.supplier_id,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'category': self.category.to_dict() if self.category else None,
            'supplier': self.supplier.to_dict() if self.supplier else None
        }

class Customer(db.Model):
    """Modelo para clientes"""
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    registration = db.Column(db.String(20), unique=True)
    cpf = db.Column(db.String(11), unique=True, nullable=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    credit_limit = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    current_debt = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    sales = db.relationship('Sale', back_populates='customer', lazy=True)
    receivables = db.relationship('Receivable', back_populates='customer', lazy=True)

    @staticmethod
    def generate_next_registration():
        """Gera o próximo número de matrícula disponível"""
        last_customer = Customer.query.order_by(Customer.registration.desc()).first()
        if last_customer and last_customer.registration:
            try:
                next_number = int(last_customer.registration) + 1
            except ValueError:
                next_number = 1001
        else:
            next_number = 1001
        return str(next_number)

    def __init__(self, **kwargs):
        if 'registration' not in kwargs:
            kwargs['registration'] = self.generate_next_registration()
        if 'credit_limit' in kwargs:
            kwargs['credit_limit'] = Decimal(str(kwargs['credit_limit']))
        if 'current_debt' in kwargs:
            kwargs['current_debt'] = Decimal(str(kwargs['current_debt']))
        super(Customer, self).__init__(**kwargs)

    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'registration': self.registration,
            'cpf': self.cpf,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0,
            'current_debt': float(self.current_debt) if self.current_debt else 0,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def update_debt(self):
        """Atualiza a dívida atual do cliente"""
        total_debt = 0
        for receivable in self.receivables:
            if receivable.status != 'paid':
                total_debt += float(receivable.remaining_amount or 0)
        self.current_debt = Decimal(str(total_debt))

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Numeric(10, 2), default=0)
    payment_method = db.Column(db.String(20))
    status = db.Column(db.String(20))
    
    # Relacionamentos
    customer = db.relationship('Customer', back_populates='sales')
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], back_populates='sales_supervised')
    items = db.relationship('SaleItem', back_populates='sale', lazy=True)
    payments = db.relationship('Payment', back_populates='sale', lazy=True)
    receivables = db.relationship('Receivable', back_populates='sale', lazy=True)
    
    def __init__(self, **kwargs):
        if 'total' in kwargs:
            kwargs['total'] = Decimal(str(kwargs['total']))
        super(Sale, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'supervisor_id': self.supervisor_id,
            'date': self.date.isoformat() if self.date else None,
            'total': float(self.total) if self.total else 0,
            'payment_method': self.payment_method,
            'status': self.status,
            'items': [item.to_dict() for item in self.items],
            'receivables': [receivable.to_dict() for receivable in self.receivables],
            'customer': self.customer.to_dict() if self.customer else None
        }

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    discount = db.Column(db.Numeric(10, 2), default=0)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Relacionamentos
    sale = db.relationship('Sale', back_populates='items', lazy=True)
    product = db.relationship('Product', back_populates='sale_items', lazy=True)
    
    def __init__(self, **kwargs):
        if 'quantity' in kwargs:
            kwargs['quantity'] = Decimal(str(kwargs['quantity']))
        if 'price' in kwargs:
            kwargs['price'] = Decimal(str(kwargs['price']))
        if 'discount' in kwargs:
            kwargs['discount'] = Decimal(str(kwargs['discount']))
        if 'subtotal' in kwargs:
            kwargs['subtotal'] = Decimal(str(kwargs['subtotal']))
        super(SaleItem, self).__init__(**kwargs)
        if not kwargs.get('subtotal'):
            self.calculate_subtotal()
    
    def calculate_subtotal(self):
        """Calcula o subtotal do item considerando preço, quantidade e desconto"""
        if self.price and self.quantity:
            subtotal = self.price * self.quantity
            if self.discount:
                subtotal = subtotal * (1 - self.discount / 100)
            self.subtotal = subtotal
    
    def to_dict(self):
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'product_code': self.product.code if self.product else None,
            'product_name': self.product.name if self.product else None,
            'quantity': float(self.quantity) if self.quantity else 0,
            'unit': self.product.unit if self.product else 'un',
            'price': float(self.price) if self.price else 0,
            'discount': float(self.discount) if self.discount else 0,
            'subtotal': float(self.subtotal) if self.subtotal else 0
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    received_amount = db.Column(db.Numeric(10, 2), nullable=True)  # Valor recebido em dinheiro
    method = db.Column(db.String(20), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    
    # Relacionamento
    sale = db.relationship('Sale', back_populates='payments', lazy=True)
    
    def __init__(self, **kwargs):
        if 'amount' in kwargs:
            kwargs['amount'] = Decimal(str(kwargs['amount']))
        if 'received_amount' in kwargs:
            kwargs['received_amount'] = Decimal(str(kwargs['received_amount']))
        super(Payment, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'amount': float(self.amount) if self.amount else 0,
            'received_amount': float(self.received_amount) if self.received_amount else 0,
            'method': self.method,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'sale': self.sale.to_dict() if self.sale else None
        }

class Receivable(db.Model):
    __tablename__ = 'receivables'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    remaining_amount = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), default='pending')  # pending, partial, paid, overdue
    description = db.Column(db.String(200))
    
    # Relacionamentos
    customer = db.relationship('Customer', back_populates='receivables')
    sale = db.relationship('Sale', back_populates='receivables')
    payments = db.relationship('ReceivablePayment', back_populates='receivable', lazy=True)

    def __init__(self, **kwargs):
        if 'amount' in kwargs:
            kwargs['amount'] = Decimal(str(kwargs['amount']))
            kwargs['remaining_amount'] = kwargs['amount']
        if 'paid_amount' in kwargs:
            kwargs['paid_amount'] = Decimal(str(kwargs['paid_amount']))
        super(Receivable, self).__init__(**kwargs)
    
    def update_remaining_amount(self):
        """Atualiza o valor restante e o status baseado no valor pago"""
        self.remaining_amount = self.amount - (self.paid_amount or Decimal('0'))
        self.update_status()
    
    def update_status(self):
        """Atualiza o status baseado na data de vencimento e valor pago"""
        today = date.today()
        
        if self.remaining_amount is None:
            self.remaining_amount = self.amount - (self.paid_amount or Decimal('0'))
            
        if self.remaining_amount <= 0:
            self.status = 'paid'
        elif (self.paid_amount or Decimal('0')) > 0:
            self.status = 'partial'
        elif self.due_date and self.due_date < today:
            self.status = 'overdue'
        else:
            self.status = 'pending'
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'sale_id': self.sale_id,
            'amount': float(self.amount),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'paid_amount': float(self.paid_amount) if self.paid_amount else 0,
            'remaining_amount': float(self.remaining_amount) if self.remaining_amount else float(self.amount),
            'status': self.status,
            'description': self.description,
            'customer_name': self.customer.name if self.customer else None,
            'payments': [payment.to_dict() for payment in self.payments]
        }

class Payable(db.Model):
    __tablename__ = 'payables'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    remaining_amount = db.Column(db.Numeric(10, 2))
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20))
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    supplier = db.relationship('Supplier', back_populates='payables')
    invoice = db.relationship('Invoice', back_populates='payable')
    payments = db.relationship('PayablePayment', back_populates='payable', lazy=True)
    
    def __init__(self, **kwargs):
        if 'amount' in kwargs:
            kwargs['amount'] = Decimal(str(kwargs['amount']))
        if 'paid_amount' in kwargs:
            kwargs['paid_amount'] = Decimal(str(kwargs['paid_amount']))
        super(Payable, self).__init__(**kwargs)
        self.update_remaining_amount()
        self.update_status()
    
    def update_remaining_amount(self):
        """Atualiza o valor restante a pagar"""
        self.remaining_amount = self.amount - (self.paid_amount or Decimal('0'))
        self.update_status()
        
    def update_status(self):
        """Atualiza o status baseado na data de vencimento e valor pago"""
        today = date.today()
        
        if self.remaining_amount is None:
            self.remaining_amount = self.amount - (self.paid_amount or Decimal('0'))
            
        if self.remaining_amount <= 0:
            self.status = 'paid'
        elif (self.paid_amount or Decimal('0')) > 0:
            self.status = 'partial'
        elif self.due_date and self.due_date < today:
            self.status = 'overdue'
        else:
            self.status = 'pending'
    
    def add_payment(self, amount, payment_method, notes=None):
        """Adiciona um pagamento à conta"""
        amount = Decimal(str(amount))
        
        if amount > self.remaining_amount:
            raise ValueError('Valor do pagamento maior que o valor restante')
            
        payment = PayablePayment(
            payable=self,
            amount=amount,
            payment_method=payment_method,
            notes=notes
        )
        
        self.paid_amount += amount
        self.update_remaining_amount()
        
        return payment
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        self.update_status()  # Atualiza o status antes de retornar
        return {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'invoice_id': self.invoice_id,
            'amount': float(self.amount),
            'paid_amount': float(self.paid_amount),
            'remaining_amount': float(self.remaining_amount) if self.remaining_amount else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'supplier': self.supplier.to_dict() if self.supplier else None
        }

class PayablePayment(db.Model):
    __tablename__ = 'payable_payments'
    id = db.Column(db.Integer, primary_key=True)
    payable_id = db.Column(db.Integer, db.ForeignKey('payables.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    payable = db.relationship('Payable', back_populates='payments')
    
    def __init__(self, **kwargs):
        if 'amount' in kwargs:
            kwargs['amount'] = Decimal(str(kwargs['amount']))
        super(PayablePayment, self).__init__(**kwargs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'payable_id': self.payable_id,
            'amount': float(self.amount) if self.amount else 0,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class CompanyInfo(db.Model):
    """Modelo para armazenar informações da empresa"""
    __tablename__ = 'company_info'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    cnpj = db.Column(db.String(18))
    ie = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip_code = db.Column(db.String(9))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    # Configurações de impressão
    printer_name = db.Column(db.String(100))
    print_header = db.Column(db.Text)
    print_footer = db.Column(db.Text)
    auto_print = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'cnpj': self.cnpj,
            'ie': self.ie,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'phone': self.phone,
            'email': self.email,
            'printer_name': self.printer_name,
            'print_header': self.print_header,
            'print_footer': self.print_footer,
            'auto_print': self.auto_print
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # low_stock, overdue_receivable, overdue_payable
    message = db.Column(db.String(200), nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reference_id = db.Column(db.Integer)  # ID do item relacionado (produto, conta a receber, etc)
    reference_type = db.Column(db.String(50))  # product, receivable, payable
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reference_id': self.reference_id,
            'reference_type': self.reference_type
        }

class Invoice(db.Model):
    __tablename__ = 'invoices'
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False, unique=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(20))
    payment_date = db.Column(db.Date)
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    supplier = db.relationship('Supplier', back_populates='invoices')
    items = db.relationship('InvoiceItem', back_populates='invoice', lazy=True)
    payable = db.relationship('Payable', back_populates='invoice', uselist=False, lazy=True)

    def __init__(self, **kwargs):
        if 'total' in kwargs:
            kwargs['total'] = Decimal(str(kwargs['total']))
        super(Invoice, self).__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'number': self.number,
            'supplier_id': self.supplier_id,
            'supplier': self.supplier.to_dict() if self.supplier else None,
            'date': self.date.isoformat() if self.date else None,
            'total': float(self.total) if self.total else 0,
            'status': self.status,
            'payment_method': self.payment_method,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'items': [item.to_dict() for item in self.items] if self.items else []
        }

class InvoiceItem(db.Model):
    __tablename__ = 'invoice_items'
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 3), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Relacionamentos
    invoice = db.relationship('Invoice', back_populates='items')
    product = db.relationship('Product', back_populates='invoice_items')

    def __init__(self, **kwargs):
        if 'quantity' in kwargs:
            kwargs['quantity'] = Decimal(str(kwargs['quantity']))
        if 'price' in kwargs:
            kwargs['price'] = Decimal(str(kwargs['price']))
        if 'total' in kwargs:
            kwargs['total'] = Decimal(str(kwargs['total']))
        super(InvoiceItem, self).__init__(**kwargs)
        if not kwargs.get('total'):
            self.total = self.quantity * self.price

    def to_dict(self):
        return {
            'id': self.id,
            'invoice_id': self.invoice_id,
            'product_id': self.product_id,
            'product': self.product.to_dict() if self.product else None,
            'quantity': float(self.quantity),
            'price': float(self.price),
            'total': float(self.total)
        }

class ReceivablePayment(db.Model):
    __tablename__ = 'receivable_payments'
    id = db.Column(db.Integer, primary_key=True)
    receivable_id = db.Column(db.Integer, db.ForeignKey('receivables.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    payment_method = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    receivable = db.relationship('Receivable', back_populates='payments')
    
    def __init__(self, **kwargs):
        if 'amount' in kwargs:
            kwargs['amount'] = Decimal(str(kwargs['amount']))
        super(ReceivablePayment, self).__init__(**kwargs)

    def to_dict(self):
        return {
            'id': self.id,
            'receivable_id': self.receivable_id,
            'amount': float(self.amount) if self.amount else 0,
            'payment_date': self.payment_date.isoformat() if self.payment_date else None,
            'payment_method': self.payment_method,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
