from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db, Sale, SaleItem, Product, Customer, Receivable, Payment, ReceivablePayment, User, CompanyInfo
from datetime import datetime, timedelta
from decimal import Decimal
from utils.printer import print_receipt

vendas_bp = Blueprint('vendas', __name__)

@vendas_bp.route('/vendas')
@login_required
def list_sales():
    """Lista todas as vendas"""
    try:
        sales = Sale.query.order_by(Sale.date.desc()).all()
        return render_template('vendas/list.html', sales=sales)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@vendas_bp.route('/vendas/nova')
@login_required
def create():
    """Página do PDV"""
    try:
        return render_template('vendas/pdv.html')
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@vendas_bp.route('/api/vendas', methods=['POST'])
@login_required
def criar_venda():
    """Cria uma nova venda"""
    try:
        data = request.get_json()
        
        # Validação dos dados
        if not data.get('items'):
            return jsonify({
                'success': False,
                'error': 'Nenhum item informado'
            })
        
        # Calcula o total da venda
        total = sum(Decimal(str(item['quantity'])) * Decimal(str(item['price'])) for item in data['items'])
        
        # Se for venda no crediário
        if data.get('payment_method') == 'crediario':
            # Verifica se tem cliente
            if not data.get('customer_id'):
                return jsonify({
                    'success': False,
                    'error': 'Cliente não informado para venda no crediário'
                })
            
            # Busca o cliente
            customer = Customer.query.get(data['customer_id'])
            if not customer:
                return jsonify({
                    'success': False,
                    'error': 'Cliente não encontrado'
                })
            
            # Verifica o limite apenas se não for uma venda autorizada
            if not data.get('authorized'):
                limite_disponivel = customer.credit_limit - customer.current_debt
                if total > limite_disponivel:
                    return jsonify({
                        'success': False,
                        'error': 'Cliente não possui limite disponível'
                    })
        
        # Cria a venda
        sale = Sale(
            customer_id=data.get('customer_id'),
            payment_method=data['payment_method'],
            supervisor_id=current_user.id,
            total=total  # Define o total da venda
        )
        
        # Adiciona os itens
        for item_data in data['items']:
            quantity = Decimal(str(item_data['quantity']))
            price = Decimal(str(item_data['price']))
            subtotal = quantity * price
            
            item = SaleItem(
                product_id=item_data['product_id'],
                quantity=quantity,
                price=price,
                subtotal=subtotal
            )
            sale.items.append(item)
            
            # Atualiza o estoque
            product = Product.query.get(item_data['product_id'])
            if product:
                product.stock -= quantity
        
        # Se for crediário, cria as parcelas
        if data.get('payment_method') == 'crediario' and data.get('receivables'):
            for receivable_data in data['receivables']:
                # Converter a string de data para objeto datetime
                due_date = datetime.strptime(receivable_data['due_date'], '%Y-%m-%d')
                # Converter o valor para Decimal
                amount = Decimal(str(receivable_data['amount']))
                
                # Cria uma descrição automática
                description = f"Venda #{sale.id} - Parcela {receivable_data.get('installment', 1)}"
                
                receivable = Receivable(
                    customer_id=data['customer_id'],
                    sale_id=sale.id,
                    amount=amount,
                    due_date=due_date,
                    status='pending',
                    remaining_amount=amount,
                    description=description
                )
                sale.receivables.append(receivable)
                
                # Atualiza a dívida do cliente
                customer = Customer.query.get(data['customer_id'])
                if customer:
                    customer.current_debt = customer.current_debt + amount
        
        db.session.add(sale)
        
        # Adiciona a venda e faz commit para gerar o ID
        db.session.commit()
        
        # Cria o registro de pagamento
        if data.get('payment_method') != 'crediario':
            payment = Payment(
                sale_id=sale.id,
                amount=total,
                received_amount=data.get('received_amount'),
                method=data['payment_method'],
                status='confirmed'
            )
            db.session.add(payment)
            db.session.commit()
        
        # Imprime o cupom se configurado
        try:
            company = CompanyInfo.query.first()
            if company and company.auto_print:
                print("Tentando imprimir cupom...")
                result = print_receipt(sale)
                print(f"Resultado da impressão: {result}")
        except Exception as e:
            print(f"Erro ao tentar imprimir: {str(e)}")
            
        return jsonify({
            'success': True,
            'message': 'Venda realizada com sucesso',
            'data': {
                'id': sale.id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@vendas_bp.route('/api/clientes/<registration>/dividas')
@login_required
def get_customer_debts(registration):
    """Retorna as dívidas de um cliente"""
    try:
        customer = Customer.query.filter_by(registration=registration).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Cliente não encontrado'})
        
        receivables = Receivable.query.filter_by(
            customer_id=customer.id,
            status='pending'
        ).all()
        
        return jsonify({
            'success': True,
            'dividas': [r.to_dict() for r in receivables]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@vendas_bp.route('/api/dividas/<int:receivable_id>/pagar', methods=['POST'])
@login_required
def pay_debt(receivable_id):
    """Registra um pagamento em uma dívida"""
    try:
        data = request.get_json()
        receivable = Receivable.query.get(receivable_id)
        if not receivable:
            return jsonify({'success': False, 'error': 'Dívida não encontrada'})
        
        # Verifica se o valor não é maior que o restante
        valor = Decimal(str(data['valor']))
        if valor > receivable.remaining_amount:
            return jsonify({
                'success': False,
                'error': 'Valor maior que o restante da dívida'
            })
        
        # Registra o pagamento
        payment = ReceivablePayment(
            receivable_id=receivable.id,
            amount=valor,
            payment_method=data['forma_pagamento']
        )
        db.session.add(payment)
        
        # Atualiza o valor pago
        receivable.paid_amount += valor
        receivable.update_remaining_amount()
        
        # Atualiza o status da dívida
        if receivable.remaining_amount == 0:
            receivable.status = 'paid'
        elif receivable.paid_amount > 0:
            receivable.status = 'partial'
        else:
            receivable.status = 'pending'
        
        # Atualiza a dívida do cliente
        if receivable.customer:
            receivable.customer.update_debt()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': receivable.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@vendas_bp.route('/api/produtos/<code>')
@login_required
def get_product(code):
    """Retorna um produto pelo código"""
    try:
        product = Product.query.filter_by(code=code).first()
        if not product:
            return jsonify({'success': False, 'error': 'Produto não encontrado'})
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@vendas_bp.route('/api/produtos/buscar')
@login_required
def search_product():
    """Busca produtos por código ou nome"""
    try:
        search = request.args.get('q', '').strip()
        if not search:
            return jsonify({'success': False, 'error': 'Digite um código ou nome para buscar'})
        
        # Busca por código exato ou nome parcial
        products = Product.query.filter(
            (Product.code == search) |
            Product.name.ilike(f'%{search}%')
        ).all()
        
        if not products:
            return jsonify({'success': False, 'error': 'Nenhum produto encontrado'})
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@vendas_bp.route('/api/clientes/<registration>')
@login_required
def get_customer(registration):
    """Retorna um cliente pela matrícula"""
    try:
        customer = Customer.query.filter_by(registration=registration).first()
        if not customer:
            return jsonify({'success': False, 'error': 'Cliente não encontrado'})
        
        return jsonify({
            'success': True,
            'customer': customer.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@vendas_bp.route('/api/sales/<int:id>')
@login_required
def get_sale(id):
    """Busca os detalhes de uma venda"""
    try:
        sale = Sale.query.get(id)
        if not sale:
            return jsonify({
                'success': False,
                'error': 'Venda não encontrada'
            })
        
        # Converte a venda para dicionário
        sale_dict = sale.to_dict()
        
        # Adiciona os itens da venda
        items = []
        total = Decimal('0')
        
        for item in sale.items:
            item_dict = item.to_dict()
            items.append(item_dict)
            # Calcula o subtotal do item
            subtotal = Decimal(str(item.quantity)) * Decimal(str(item.price))
            item_dict['subtotal'] = float(subtotal)
            total += subtotal
        
        sale_dict['items'] = items
        sale_dict['total'] = float(total)
        
        # Adiciona as parcelas se for venda a prazo
        if sale.payment_method == 'crediario':
            sale_dict['receivables'] = [r.to_dict() for r in sale.receivables]
        
        return jsonify({
            'success': True,
            'data': sale_dict
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@vendas_bp.route('/api/sales/<int:id>/print')
@login_required
def print_sale(id):
    """Imprime uma venda específica"""
    try:
        # Busca a venda
        sale = Sale.query.get(id)
        if not sale:
            return jsonify({
                'success': False,
                'error': 'Venda não encontrada'
            }), 404
            
        # Busca as configurações da empresa
        company = CompanyInfo.query.first()
        if not company:
            return jsonify({
                'success': False,
                'error': 'Configurações da empresa não encontradas'
            }), 404
            
        # Tenta imprimir o cupom
        result = print_receipt(sale)
        
        return jsonify({
            'success': True,
            'message': 'Cupom enviado para impressão'
        })
        
    except Exception as e:
        print(f"Erro ao imprimir venda: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@vendas_bp.route('/api/vendas/autorizar', methods=['POST'])
@login_required
def autorizar_venda():
    """Autoriza uma venda para cliente sem limite"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Busca o usuário
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({
                'success': False,
                'error': 'Usuário não encontrado'
            })
        
        # Verifica a senha
        if not user.check_password(password):
            return jsonify({
                'success': False,
                'error': 'Senha incorreta'
            })
        
        # Verifica se o usuário tem permissão
        if user.role not in ['supervisor', 'gerente', 'admin']:
            return jsonify({
                'success': False,
                'error': 'Usuário sem permissão para autorizar vendas'
            })
        
        return jsonify({
            'success': True,
            'message': 'Venda autorizada com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })
