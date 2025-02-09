from flask import Flask
from models import db, Customer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def test_customer():
    with app.app_context():
        # Teste 1: Buscar por matrícula
        customer = Customer.query.filter(
            Customer.registration == '1103'
        ).first()
        print("\nTeste 1 - Busca por matrícula 1103:")
        print(f"Cliente encontrado: {customer}")
        if customer:
            print(f"- Nome: {customer.name}")
            print(f"- CPF: {customer.cpf}")
            print(f"- Matrícula: {customer.registration}")
        
        # Teste 2: Buscar por CPF
        customer = Customer.query.filter(
            Customer.cpf == '06911499500'
        ).first()
        print("\nTeste 2 - Busca por CPF 06911499500:")
        print(f"Cliente encontrado: {customer}")
        if customer:
            print(f"- Nome: {customer.name}")
            print(f"- CPF: {customer.cpf}")
            print(f"- Matrícula: {customer.registration}")
        
        # Teste 3: Listar todos os clientes
        customers = Customer.query.all()
        print("\nTeste 3 - Todos os clientes:")
        for customer in customers:
            print(f"- {customer.id}: {customer.name} (CPF: {customer.cpf}, Matrícula: {customer.registration})")

if __name__ == '__main__':
    test_customer()
