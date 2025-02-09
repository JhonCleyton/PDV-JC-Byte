from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def add_columns():
    with app.app_context():
        # Adiciona novas colunas à tabela products
        db.session.execute('ALTER TABLE products ADD COLUMN max_stock DECIMAL(10,3) DEFAULT 0')
        db.session.execute('ALTER TABLE products ADD COLUMN unit VARCHAR(10) DEFAULT "un"')
        db.session.execute('ALTER TABLE products ADD COLUMN barcode VARCHAR(20)')
        db.session.execute('ALTER TABLE products ADD COLUMN status VARCHAR(20) DEFAULT "active"')
        
        # Remove colunas não utilizadas
        db.session.execute('ALTER TABLE products DROP COLUMN markup')
        db.session.execute('ALTER TABLE products DROP COLUMN expiry_date')
        
        # Altera o tipo das colunas existentes
        db.session.execute('ALTER TABLE products ALTER COLUMN min_stock TYPE DECIMAL(10,3)')
        db.session.execute('ALTER TABLE products ALTER COLUMN stock TYPE DECIMAL(10,3)')
        
        db.session.commit()
        print("Colunas adicionadas com sucesso!")

if __name__ == '__main__':
    add_columns()
