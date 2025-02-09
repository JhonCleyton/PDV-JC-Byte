from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Receivable, ReceivablePayment, Customer, Sale
from datetime import datetime, date

contas_a_receber_bp = Blueprint('contas_a_receber', __name__)

@contas_a_receber_bp.route('/contas_a_receber/manage')
@login_required
def manage_contas_a_receber():
    """Página de gerenciamento de contas a receber"""
    return render_template('contas_a_receber/manage.html')

@contas_a_receber_bp.route('/api/contas_a_receber/list')
@login_required
def list_contas_a_receber():
    """Lista todas as contas a receber com filtros"""
    customer_id = request.args.get('customer_id', type=int)
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Receivable.query
    
    if customer_id:
        query = query.filter(Receivable.customer_id == customer_id)
    
    if status:
        query = query.filter(Receivable.status == status)
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Receivable.due_date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Receivable.due_date <= end)
    
    contas_a_receber = query.order_by(Receivable.due_date).all()
    return jsonify({
        'success': True,
        'data': [conta_a_receber.to_dict() for conta_a_receber in contas_a_receber]
    })

@contas_a_receber_bp.route('/api/contas_a_receber', methods=['POST'])
@login_required
def create_conta_a_receber():
    """Cria uma nova conta a receber manualmente"""
    try:
        data = request.get_json()
        
        customer = Customer.query.get(data['customer_id'])
        if not customer:
            return jsonify({
                'success': False,
                'error': 'Cliente não encontrado'
            }), 404
        
        conta_a_receber = Receivable(
            customer_id=customer.id,
            amount=data['amount'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            description=data.get('description', ''),
            status='pending'
        )
        
        db.session.add(conta_a_receber)
        db.session.commit()
        
        customer.update_debt()
        
        return jsonify({
            'success': True,
            'data': conta_a_receber.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas_a_receber/<int:id>/payment', methods=['POST'])
@login_required
def add_payment(id):
    """Adiciona um pagamento a uma conta"""
    try:
        data = request.get_json()
        conta_a_receber = Receivable.query.get_or_404(id)
        
        if conta_a_receber.status == 'paid':
            return jsonify({
                'success': False,
                'error': 'Esta conta já está paga'
            }), 400
        
        payment = conta_a_receber.add_payment(
            amount=data['amount'],
            payment_method=data['payment_method'],
            notes=data.get('notes')
        )
        
        db.session.add(payment)
        db.session.commit()
        
        conta_a_receber.customer.update_debt()
        
        return jsonify({
            'success': True,
            'data': conta_a_receber.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas_a_receber/customer/<int:customer_id>')
@login_required
def get_customer_contas_a_receber(customer_id):
    """Retorna todas as contas a receber de um cliente"""
    customer = Customer.query.get_or_404(customer_id)
    
    contas_a_receber = Receivable.query.filter(
        Receivable.customer_id == customer_id,
        Receivable.status.in_(['pending', 'partial', 'overdue'])
    ).order_by(Receivable.due_date).all()
    
    return jsonify({
        'success': True,
        'data': {
            'customer': customer.to_dict(),
            'contas_a_receber': [conta_a_receber.to_dict() for conta_a_receber in contas_a_receber]
        }
    })

@contas_a_receber_bp.route('/api/contas_a_receber/bulk-payment', methods=['POST'])
@login_required
def bulk_payment():
    """Processa o pagamento de múltiplas contas"""
    try:
        data = request.get_json()
        total_amount = float(data['amount'])
        conta_a_receber_ids = data['conta_a_receber_ids']
        payment_method = data['payment_method']
        
        # Ordena as contas por data de vencimento
        contas_a_receber = Receivable.query.filter(
            Receivable.id.in_(conta_a_receber_ids)
        ).order_by(Receivable.due_date).all()
        
        if not contas_a_receber:
            return jsonify({
                'success': False,
                'error': 'Nenhuma conta encontrada'
            }), 404
        
        # Processa o pagamento em ordem
        remaining_amount = total_amount
        payments = []
        
        for conta_a_receber in contas_a_receber:
            if remaining_amount <= 0:
                break
                
            # Determina o valor a ser pago nesta conta
            payment_amount = min(remaining_amount, float(conta_a_receber.remaining_amount))
            
            # Registra o pagamento
            payment = conta_a_receber.add_payment(
                amount=payment_amount,
                payment_method=payment_method,
                notes=f'Pagamento em lote - R$ {total_amount:.2f}'
            )
            
            payments.append(payment)
            db.session.add(payment)
            
            remaining_amount -= payment_amount
        
        db.session.commit()
        
        # Atualiza a dívida do cliente
        contas_a_receber[0].customer.update_debt()
        
        return jsonify({
            'success': True,
            'data': {
                'total_paid': total_amount - remaining_amount,
                'remaining_amount': remaining_amount,
                'contas_a_receber': [conta_a_receber.to_dict() for conta_a_receber in contas_a_receber]
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas_a_receber/total', methods=['GET'])
@login_required
def get_total_contas_a_receber():
    """Retorna o total de contas a receber"""
    try:
        total = db.session.query(
            db.func.sum(Receivable.amount)
        ).filter(
            Receivable.status != 'paid'
        ).scalar() or 0

        return jsonify({
            'success': True,
            'data': {
                'total': float(total)
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
