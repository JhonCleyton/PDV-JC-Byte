from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/pdv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    receivables = db.relationship('Receivable', back_populates='customer')

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    payables = db.relationship('Payable', back_populates='supplier')

class Receivable(db.Model):
    __tablename__ = 'receivables'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    paid_amount = db.Column(db.Numeric(10, 2), default=0)
    remaining_amount = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), default='pending')
    customer = db.relationship('Customer', back_populates='receivables')

class Payable(db.Model):
    __tablename__ = 'payables'
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'))
    amount = db.Column(db.Numeric(10, 2))
    due_date = db.Column(db.Date)
    paid_amount = db.Column(db.Numeric(10, 2))
    remaining_amount = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20))
    supplier = db.relationship('Supplier', back_populates='payables')

with app.app_context():
    try:
        # Verifica contas a receber
        receivables = Receivable.query.all()
        print(f"\nTotal de contas a receber: {len(receivables)}")
        
        if not receivables:
            print("\nNão há contas a receber no banco.")
        else:
            print("\nContas a receber existentes:")
            for r in receivables:
                print(f"ID: {r.id}")
                print(f"Cliente ID: {r.customer_id}")
                print(f"Vencimento: {r.due_date}")
                print(f"Valor: {r.amount}")
                print(f"Valor Pago: {r.paid_amount}")
                print(f"Valor Restante: {r.remaining_amount}")
                print(f"Status: {r.status}")
                print("---")
    except Exception as e:
        print(f"Erro ao consultar contas a receber: {str(e)}")
        print("Verificando se a tabela existe...")
        
        # Verifica se a tabela existe
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print("\nTabelas no banco:")
        for table in tables:
            print(f"- {table}")
            if table == 'receivables':
                print("\nColunas na tabela receivables:")
                for column in inspector.get_columns(table):
                    print(f"- {column['name']}: {column['type']}")
