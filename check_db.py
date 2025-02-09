from models import db, Receivable, Customer, Sale
from app import create_app
from datetime import datetime

app = create_app()

def check_db():
    with app.app_context():
        # Verifica se a tabela existe
        inspector = db.engine.reflector
        tables = inspector.get_table_names()
        print("\nTabelas no banco:")
        for table in tables:
            print(f"- {table}")
            
        if 'customers' in tables:
            # Mostra as colunas da tabela
            columns = inspector.get_columns('customers')
            print("\nColunas da tabela customers:")
            for column in columns:
                print(f"- {column['name']}: {column['type']}")
            
            # Lista todos os clientes
            customers = Customer.query.all()
            print("\nClientes cadastrados:")
            for customer in customers:
                print(f"\nCliente {customer.id}:")
                print(f"- Nome: {customer.name}")
                print(f"- CPF: {customer.cpf}")
                print(f"- Matrícula: {customer.registration}")
                print(f"- Email: {customer.email}")
                print(f"- Telefone: {customer.phone}")
                print(f"- Limite: {customer.credit_limit}")
                print(f"- Dívida: {customer.current_debt}")
                print(f"- Status: {customer.status}")
        else:
            print("\nTabela customers não existe!")
            
        # Tenta buscar cliente específico
        customer = Customer.query.filter(
            Customer.registration == '1103'
        ).first()
        
        if customer:
            print(f"\nTeste - Cliente 1103:")
            print(f"- Nome: {customer.name}")
            print(f"- CPF: {customer.cpf}")
            print(f"- Matrícula: {customer.registration}")
        else:
            print("\nCliente 1103 não encontrado!")

        # Verifica contas a receber
        receivables = Receivable.query.all()
        print(f"\nTotal de contas a receber: {len(receivables)}")
        
        if not receivables:
            print("\nNão há contas a receber no banco.")
            
            # Vamos criar uma conta a receber de teste
            # Primeiro precisamos de um cliente
            customer = Customer.query.first()
            if not customer:
                customer = Customer(
                    name="Cliente Teste",
                    registration="001",
                    credit_limit=1000.00
                )
                db.session.add(customer)
                db.session.commit()
            
            # Agora criamos uma conta a receber
            receivable = Receivable(
                customer_id=customer.id,
                amount=100.00,
                due_date=datetime.now(),
                description="Conta a receber de teste"
            )
            db.session.add(receivable)
            db.session.commit()
            print("\nCriada conta a receber de teste.")
        else:
            print("\nContas a receber existentes:")
            for r in receivables:
                print(f"ID: {r.id}")
                print(f"Cliente: {r.customer.name if r.customer else 'N/A'}")
                print(f"Vencimento: {r.due_date}")
                print(f"Valor: {r.amount}")
                print(f"Status: {r.status}")
                print("---")

if __name__ == '__main__':
    check_db()
