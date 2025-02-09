import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from models import db, Product
from decimal import Decimal
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def recreate_products_table():
    with app.app_context():
        # Backup dos dados existentes
        products_data = []
        try:
            old_products = db.session.execute(text('SELECT id, code, name, description, cost_price, selling_price, min_stock, stock, category_id, supplier_id, created_at FROM products')).fetchall()
            for p in old_products:
                products_data.append({
                    'id': p[0],
                    'code': p[1],
                    'name': p[2],
                    'description': p[3],
                    'cost_price': Decimal(str(p[4])) if p[4] else Decimal('0'),
                    'selling_price': Decimal(str(p[5])) if p[5] else Decimal('0'),
                    'min_stock': Decimal(str(p[6])) if p[6] else Decimal('0'),
                    'stock': Decimal(str(p[7])) if p[7] else Decimal('0'),
                    'category_id': p[8],
                    'supplier_id': p[9],
                    'created_at': datetime.strptime(p[10], '%Y-%m-%d %H:%M:%S.%f') if p[10] else datetime.utcnow()
                })
        except Exception as e:
            print(f"Erro ao fazer backup dos dados: {str(e)}")
            return

        # Recria a tabela products
        try:
            db.session.execute(text('DROP TABLE IF EXISTS products'))
            db.session.commit()
            
            # Cria a nova tabela com todas as colunas
            db.create_all()
            
            # Restaura os dados
            for data in products_data:
                product = Product(
                    code=data['code'],
                    name=data['name'],
                    description=data['description'],
                    cost_price=data['cost_price'],
                    selling_price=data['selling_price'],
                    min_stock=data['min_stock'],
                    max_stock=Decimal('0'),
                    stock=data['stock'],
                    unit='un',
                    status='active',
                    category_id=data['category_id'],
                    supplier_id=data['supplier_id']
                )
                product.created_at = data['created_at']
                db.session.add(product)
            
            db.session.commit()
            print("Tabela products recriada com sucesso!")
            
        except Exception as e:
            print(f"Erro ao recriar tabela: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    recreate_products_table()
