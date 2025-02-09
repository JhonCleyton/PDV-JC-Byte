from app import app, db
from models import *
import os

def recreate_database():
    """Recria o banco de dados com a estrutura atualizada"""
    with app.app_context():
        # Remover banco de dados existente
        if os.path.exists('database.db'):
            os.remove('database.db')
        
        # Criar tabelas
        db.create_all()
        
        # Criar usuário admin
        admin = User(
            name='Administrador',
            username='admin',
            role='admin',
            status='active'
        )
        admin.set_password('admin')
        db.session.add(admin)
        
        # Criar algumas categorias básicas
        categories = [
            Category(name='Alimentos'),
            Category(name='Bebidas'),
            Category(name='Limpeza'),
            Category(name='Higiene'),
            Category(name='Outros')
        ]
        db.session.add_all(categories)
        
        db.session.commit()

if __name__ == '__main__':
    recreate_database()
