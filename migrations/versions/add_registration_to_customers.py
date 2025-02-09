"""add registration to customers

Revision ID: add_registration_to_customers
Revises: 191810979140
Create Date: 2024-01-19 11:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'add_registration_to_customers'
down_revision = '191810979140'
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona a coluna registration se não existir
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('customers')]
    if 'registration' not in columns:
        op.add_column('customers', sa.Column('registration', sa.String(20), unique=True))
    
    # Atualiza os registros existentes
    conn.execute(text("""
        WITH numbered_customers AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY id) as row_num
            FROM customers
            WHERE registration IS NULL
        )
        UPDATE customers
        SET registration = PRINTF('%04d', numbered_customers.row_num)
        FROM numbered_customers
        WHERE customers.id = numbered_customers.id;
    """))

def downgrade():
    # Remove a coluna registration
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('customers')]
    if 'registration' in columns:
        op.drop_column('customers', 'registration')
