from models import db, Product, Receivable, Payable, Notification
from datetime import datetime, timedelta, date
from sqlalchemy import and_

def check_notifications():
    """Verifica e gera notificações para diversos eventos do sistema"""
    current_datetime = datetime.now()
    current_date = current_datetime.date()
    
    # Contas a receber vencendo em 5 dias
    receivables = Receivable.query.filter(
        and_(
            Receivable.status == 'pending',
            Receivable.due_date <= current_date + timedelta(days=5),
            Receivable.due_date >= current_date
        )
    ).all()
    
    for receivable in receivables:
        days_until = (receivable.due_date - current_date).days
        create_notification(
            'receivable_due',
            f'Conta a receber de R$ {receivable.amount:.2f} vence em {days_until} dias',
            receivable.id
        )

    # Contas a pagar vencendo em 5 dias
    payables = Payable.query.filter(
        and_(
            Payable.status == 'pending',
            Payable.due_date <= current_date + timedelta(days=5),
            Payable.due_date >= current_date
        )
    ).all()
    
    for payable in payables:
        days_until = (payable.due_date - current_date).days
        create_notification(
            'payable_due',
            f'Conta a pagar de R$ {payable.amount:.2f} vence em {days_until} dias',
            payable.id
        )

    # Produtos com validade próxima (30 dias)
    products = Product.query.filter(
        and_(
            Product.expiry_date <= current_date + timedelta(days=30),
            Product.expiry_date >= current_date,
            Product.status == 'active'
        )
    ).all()
    
    for product in products:
        days_until = (product.expiry_date - current_date).days
        create_notification(
            'product_expiry',
            f'Produto {product.name} vence em {days_until} dias',
            product.id
        )

    # Produtos com estoque baixo
    low_stock_products = Product.query.filter(
        and_(
            Product.stock <= Product.min_stock,
            Product.status == 'active'
        )
    ).all()
    
    for product in low_stock_products:
        if product.stock == 0:
            create_notification(
                'stock_critical',
                f'CRÍTICO: Produto {product.name} está sem estoque!',
                product.id
            )
        else:
            create_notification(
                'stock_low',
                f'Estoque baixo: Produto {product.name} ({product.stock} {product.unit})',
                product.id
            )

def create_notification(type, message, reference_id=None):
    """Cria uma nova notificação se não existir uma similar não lida"""
    existing = Notification.query.filter_by(
        type=type,
        reference_id=reference_id,
        read=False
    ).first()
    
    if not existing:
        notification = Notification(
            type=type,
            message=message,
            reference_id=reference_id
        )
        db.session.add(notification)
        db.session.commit()
