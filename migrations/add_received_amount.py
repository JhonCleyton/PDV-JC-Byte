from alembic import op
import sqlalchemy as sa
from decimal import Decimal

# revision identifiers, used by Alembic.
revision = 'add_received_amount'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Adiciona a coluna received_amount na tabela payments
    op.add_column('payments', sa.Column('received_amount', sa.Numeric(10, 2), nullable=True))

def downgrade():
    # Remove a coluna received_amount da tabela payments
    op.drop_column('payments', 'received_amount')
