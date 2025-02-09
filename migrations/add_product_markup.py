from flask import current_app
from flask_migrate import Migrate
from models import db
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Adiciona a coluna markup
    op.add_column('products', sa.Column('markup', sa.Numeric(10, 2), nullable=False, server_default='0'))
    
    # Atualiza o preço de venda dos produtos existentes
    connection = op.get_bind()
    connection.execute("""
        UPDATE products 
        SET markup = ((selling_price / cost_price - 1) * 100)::numeric(10,2)
        WHERE cost_price > 0 AND selling_price > 0;
    """)

def downgrade():
    # Remove a coluna markup
    op.drop_column('products', 'markup')
