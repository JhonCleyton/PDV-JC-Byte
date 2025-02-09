from models import db, Payable
from app import app

with app.app_context():
    payables = Payable.query.all()
    print('\nContas a pagar:')
    for p in payables:
        print(f'ID: {p.id}')
        print(f'Valor: {p.amount}')
        print(f'Pago: {p.paid_amount}')
        print(f'Restante: {p.remaining_amount}')
        print(f'Status: {p.status}')
        print('-' * 50)
