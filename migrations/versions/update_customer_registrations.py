"""update customer registrations

Revision ID: update_customer_registrations
Revises: add_registration_to_customers
Create Date: 2025-02-08 17:54:06.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'update_customer_registrations'
down_revision = 'add_registration_to_customers'
branch_labels = None
depends_on = None

def upgrade():
    # Atualizar as matrículas dos clientes existentes
    connection = op.get_bind()
    
    # Buscar todos os clientes ordenados por ID
    result = connection.execute(text('SELECT id FROM customers ORDER BY id ASC'))
    customers = result.fetchall()
    
    # Atualizar cada cliente com uma nova matrícula começando em 1001
    for i, customer in enumerate(customers, start=1):
        new_registration = str(1000 + i)
        connection.execute(
            text('UPDATE customers SET registration = :reg WHERE id = :id'),
            {'reg': new_registration, 'id': customer[0]}
        )

def downgrade():
    # Não é possível reverter esta migração de forma segura
    pass
