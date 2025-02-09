from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Sale, SaleItem, Payment, Product, Customer, Receivable, User, CompanyInfo
from datetime import datetime, date, timedelta
import traceback

vendas = Blueprint('vendas', __name__)

@vendas.route('/api/sales', methods=['GET'])
@login_required
def get_sales():
    """Retorna todas as vendas"""
    try:
        sales = Sale.query.all()
        return jsonify({
            'success': True,
            'data': [sale.to_dict() for sale in sales]
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendas.route('/api/sales/<int:id>', methods=['GET'])
@login_required
def get_sale(id):
    """Retorna uma venda específica"""
    try:
        sale = Sale.query.get_or_404(id)
        return jsonify({
            'success': True,
            'data': sale.to_dict()
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendas.route('/api/sales', methods=['POST'])
@login_required
def create_sale():
    """Cria uma nova venda"""
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data.get('customer_id') or not data.get('items'):
            return jsonify({
                'success': False,
                'error': 'Customer and items are required'
            }), 400
        
        # Buscar cliente
        customer = Customer.query.get(data['customer_id'])
        if not customer:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        # Calcular total da venda
        total = sum(float(item['total']) for item in data['items'])
        
        # Se for venda a crédito
        if data.get('payment_method') == 'credit':
            current_debt = float(customer.current_debt) if customer.current_debt else 0
            credit_limit = float(customer.credit_limit) if customer.credit_limit else 0
            
            # Verificar se excede limite de crédito
            if current_debt + total > credit_limit:
                # Verificar supervisor
                if not data.get('supervisor_id'):
                    return jsonify({
                        'success': False,
                        'error': 'Supervisor authorization required'
                    }), 401
                
                # Buscar usuário supervisor
                supervisor = User.query.get(data['supervisor_id'])
                if not supervisor or supervisor.role not in ['admin', 'manager', 'supervisor']:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid supervisor authorization'
                    }), 401

        # Criar venda
        sale = Sale(
            customer_id=data['customer_id'],
            payment_method=data.get('payment_method', 'cash'),
            total=total,
            status='paid' if data.get('payment_method') != 'credit' else 'pending',
            supervisor_id=data.get('supervisor_id')
        )
        
        db.session.add(sale)
        
        # Criar itens da venda
        for item_data in data['items']:
            product = Product.query.get(item_data['product_id'])
            if not product:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Product {item_data["product_id"]} not found'
                }), 404
            
            if product.stock < float(item_data['quantity']):
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Insufficient stock for product {product.name}'
                }), 400
            
            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=float(item_data['quantity']),
                price=float(item_data['unit_price']),
                discount=float(item_data.get('discount', 0))
            )
            
            # Atualizar estoque
            product.stock -= float(item_data['quantity'])
            db.session.add(sale_item)
        
        # Se for venda a crédito, criar conta a receber
        if data.get('payment_method') == 'credit':
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            receivable = Receivable(
                customer_id=customer.id,
                sale_id=sale.id,
                amount=total,
                due_date=due_date,
                status='pending',
                description=f'Venda a crédito #{sale.id}'
            )
            db.session.add(receivable)
            customer.update_debt()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': sale.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendas.route('/api/sales/<int:id>', methods=['PUT'])
@login_required
def update_sale(id):
    """Atualiza uma venda"""
    try:
        sale = Sale.query.get_or_404(id)
        data = request.get_json()
        
        # Não permitir alterar vendas finalizadas
        if sale.status == 'paid':
            return jsonify({
                'success': False,
                'error': 'Não é possível alterar uma venda finalizada'
            }), 400
        
        if data.get('status'):
            sale.status = data['status']
            
            # Se a venda foi cancelada, devolver os produtos ao estoque
            if sale.status == 'cancelled':
                for item in sale.items:
                    item.product.stock += item.quantity
                    
                # Cancelar as contas a receber
                for receivable in sale.customer.receivables:
                    if receivable.description == f'Venda #{sale.id}':
                        receivable.status = 'cancelled'
                        sale.customer.update_debt()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': sale.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendas.route('/api/sales/<int:id>', methods=['DELETE'])
@login_required
def delete_sale(id):
    """Exclui uma venda"""
    try:
        sale = Sale.query.get_or_404(id)
        
        # Não permitir excluir vendas finalizadas
        if sale.status == 'paid':
            return jsonify({
                'success': False,
                'error': 'Não é possível excluir uma venda finalizada'
            }), 400
        
        # Devolver os produtos ao estoque
        for item in sale.items:
            item.product.stock += item.quantity
            
        # Excluir as contas a receber
        for receivable in sale.customer.receivables:
            if receivable.description == f'Venda #{sale.id}':
                db.session.delete(receivable)
                sale.customer.update_debt()
        
        db.session.delete(sale)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Venda excluída com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendas.route('/api/sales/today', methods=['GET'])
@login_required
def get_sales_today():
    """Retorna as vendas do dia"""
    try:
        today = datetime.now().date()
        sales = Sale.query.filter(
            db.func.date(Sale.date) == today
        ).all()
        total = sum(float(sale.total) for sale in sales)
        return jsonify({
            'success': True,
            'data': {
                'count': len(sales),
                'total': total
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendas.route('/api/sales/recent', methods=['GET'])
@login_required
def get_recent_sales():
    """Retorna as vendas mais recentes"""
    try:
        sales = Sale.query.order_by(Sale.date.desc()).limit(5).all()
        return jsonify({
            'success': True,
            'data': [sale.to_dict() for sale in sales]
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendas.route('/sales/manage')
@login_required
def manage_sales():
    """Página de gerenciamento de vendas"""
    return render_template('sales/manage.html')

@vendas.route('/api/sales/list')
@login_required
def list_sales():
    """Lista todas as vendas com filtros"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    payment_method = request.args.get('payment_method')
    status = request.args.get('status')
    
    query = Sale.query
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(db.func.date(Sale.date) >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(db.func.date(Sale.date) <= end)
    
    if payment_method:
        query = query.filter(Sale.payment_method == payment_method)
    
    if status:
        query = query.filter(Sale.status == status)
    
    sales = query.order_by(Sale.date.desc()).all()
    return jsonify({
        'success': True,
        'data': [sale.to_dict() for sale in sales]
    })

@vendas.route('/api/sales/print/<int:id>')
@login_required
def print_sale(id):
    """Imprime o comprovante de uma venda"""
    sale = Sale.query.get_or_404(id)
    company = CompanyInfo.query.first()
    
    if not company:
        return jsonify({
            'success': False,
            'error': 'Configurações da empresa não encontradas'
        }), 404
    
    # Formata o cabeçalho
    header = company.print_header.format(
        company_name=company.name,
        cnpj=company.cnpj,
        ie=company.ie,
        address=company.address,
        city=company.city,
        state=company.state
    )
    
    # Formata o rodapé
    footer = company.print_footer.format(
        datetime=sale.date.strftime('%d/%m/%Y %H:%M:%S')
    )
    
    # Monta o conteúdo do cupom
    content = []
    content.append(header)
    content.append('-' * 40)
    content.append(f'VENDA #{sale.id}')
    content.append(f'Data: {sale.date.strftime("%d/%m/%Y %H:%M:%S")}')
    if sale.customer:
        content.append(f'Cliente: {sale.customer.name}')
        content.append(f'Matrícula: {sale.customer.registration}')
    content.append('-' * 40)
    content.append('ITENS:')
    for item in sale.items:
        content.append(f'{item.quantity:>6.3f} x {item.price:>8.2f} = {item.total:>8.2f}  {item.product.name}')
    content.append('-' * 40)
    content.append(f'TOTAL: R$ {sale.total:.2f}')
    content.append(f'Forma de pagamento: {sale.payment_method}')
    
    if sale.payment_method == 'credit':
        content.append('-' * 40)
        content.append('Assinatura do Cliente:')
        content.append('_' * 40)
    
    content.append('-' * 40)
    content.append(footer)
    
    # Atualiza o controle de impressão
    sale.printed = True
    sale.print_count += 1
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'content': '\n'.join(content),
            'printer': company.printer_name
        }
    })
