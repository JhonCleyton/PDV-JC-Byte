from app import app, db
from models import Customer

with app.app_context():
    print('Clientes:')
    for c in Customer.query.all():
        print(f'- {c.id}: {c.name} (CPF: {c.cpf}, Matrícula: {c.registration})')
