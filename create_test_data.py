from app import app, db
from models import Customer, Receivable
from datetime import datetime, timedelta
from decimal import Decimal

def create_test_data():
    with app.app_context():
        # Criar um cliente de teste
        customer = Customer(
            name='Cliente Teste',
            registration='12345',
            cpf='12345678901',
            email='teste@teste.com',
            credit_limit=1000.00
        )
        db.session.add(customer)
        db.session.commit()
        
        # Criar algumas contas a receber
        today = datetime.now()
        
        # Conta 1 - Vencimento hoje, parcialmente paga
        receivable1 = Receivable(
            customer_id=customer.id,
            amount=500.00,
            due_date=today,
            paid_amount=200.00,
            remaining_amount=300.00,
            status='partial'
        )
        
        # Conta 2 - Vencimento em 15 dias, não paga
        receivable2 = Receivable(
            customer_id=customer.id,
            amount=750.00,
            due_date=today + timedelta(days=15),
            paid_amount=0.00,
            remaining_amount=750.00,
            status='pending'
        )
        
        # Conta 3 - Vencida há 5 dias, não paga
        receivable3 = Receivable(
            customer_id=customer.id,
            amount=1000.00,
            due_date=today - timedelta(days=5),
            paid_amount=0.00,
            remaining_amount=1000.00,
            status='overdue'
        )
        
        db.session.add_all([receivable1, receivable2, receivable3])
        db.session.commit()
        
        print("Dados de teste criados com sucesso!")
        print("\nContas a receber criadas:")
        for r in [receivable1, receivable2, receivable3]:
            print(f"ID: {r.id}")
            print(f"Valor: R$ {r.amount}")
            print(f"Vencimento: {r.due_date}")
            print(f"Status: {r.status}")
            print("---")

if __name__ == '__main__':
    create_test_data()
