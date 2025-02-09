from models import db, Sale, SaleItem
from app import app
from datetime import datetime

with app.app_context():
    # Verifica todas as vendas
    sales = Sale.query.all()
    print('\nVendas cadastradas:')
    for sale in sales:
        print(f'ID: {sale.id}')
        print(f'Data: {sale.date}')
        print(f'Total: {sale.total}')
        print('Itens:')
        for item in sale.items:
            print(f'  - Produto: {item.product.name}')
            print(f'    Quantidade: {item.quantity}')
            print(f'    Preço: {item.price}')
            print(f'    Subtotal: {item.subtotal}')
        print('-' * 50)
