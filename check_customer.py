from models import db, Customer
from app import app

with app.app_context():
    customer = Customer.query.filter_by(registration='1103').first()
    if customer:
        print(f"\nCliente encontrado:")
        print(f"- Nome: {customer.name}")
        print(f"- ID: {customer.id}")
        print(f"- Matrícula: {customer.registration}")
        print(f"- CPF: {customer.cpf}")
        print(f"- Limite: {customer.credit_limit}")
        print(f"- Dívida: {customer.current_debt}")
    else:
        print("\nCliente não encontrado!")
