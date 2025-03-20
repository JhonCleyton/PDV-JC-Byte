"""Alterando campos numéricos para Numeric

Revision ID: 44e9ecac3ceb
Revises: 36b295450aac
Create Date: 2025-01-18 21:06:47.994495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44e9ecac3ceb'
down_revision = '36b295450aac'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('payable', schema=None) as batch_op:
        batch_op.alter_column('amount',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)

    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.alter_column('amount',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)

    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.add_column(sa.Column('description', sa.String(length=200), nullable=True))
        batch_op.alter_column('cost_price',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)
        batch_op.alter_column('markup',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)
        batch_op.alter_column('selling_price',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)

    with op.batch_alter_table('receivable', schema=None) as batch_op:
        batch_op.alter_column('amount',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)

    with op.batch_alter_table('sale', schema=None) as batch_op:
        batch_op.alter_column('total',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)

    with op.batch_alter_table('sale_item', schema=None) as batch_op:
        batch_op.alter_column('price',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)
        batch_op.alter_column('discount',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=True)
        batch_op.alter_column('total',
               existing_type=sa.FLOAT(),
               type_=sa.Numeric(precision=10, scale=2),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sale_item', schema=None) as batch_op:
        batch_op.alter_column('total',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)
        batch_op.alter_column('discount',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=True)
        batch_op.alter_column('price',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)

    with op.batch_alter_table('sale', schema=None) as batch_op:
        batch_op.alter_column('total',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)

    with op.batch_alter_table('receivable', schema=None) as batch_op:
        batch_op.alter_column('amount',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)

    with op.batch_alter_table('product', schema=None) as batch_op:
        batch_op.alter_column('selling_price',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)
        batch_op.alter_column('markup',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)
        batch_op.alter_column('cost_price',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)
        batch_op.drop_column('description')

    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.alter_column('amount',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)

    with op.batch_alter_table('payable', schema=None) as batch_op:
        batch_op.alter_column('amount',
               existing_type=sa.Numeric(precision=10, scale=2),
               type_=sa.FLOAT(),
               existing_nullable=False)

    # ### end Alembic commands ###
