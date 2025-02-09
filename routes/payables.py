from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Payable, PayablePayment, Supplier, Invoice
from datetime import datetime, date

contas_a_pagar_bp = Blueprint('contas_a_pagar', __name__)

@contas_a_pagar_bp.route('/contas_a_pagar/manage')
@login_required
def manage_contas_a_pagar():
    """Página de gerenciamento de contas a pagar"""
    return render_template('contas_a_pagar/manage.html')

@contas_a_pagar_bp.route('/api/contas_a_pagar/list')
@login_required
def list_contas_a_pagar():
    """Lista todas as contas a pagar com filtros"""
    supplier_id = request.args.get('supplier_id', type=int)
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Payable.query
    
    if supplier_id:
        query = query.filter(Payable.supplier_id == supplier_id)
    
    if status:
        query = query.filter(Payable.status == status)
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Payable.due_date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Payable.due_date <= end)
    
    contas_a_pagar = query.order_by(Payable.due_date).all()
    return jsonify({
        'success': True,
        'data': [conta_a_pagar.to_dict() for conta_a_pagar in contas_a_pagar]
    })

@contas_a_pagar_bp.route('/api/contas_a_pagar', methods=['POST'])
@login_required
def create_conta_a_pagar():
    """Cria uma nova conta a pagar manualmente"""
    try:
        data = request.get_json()
        
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({
                'success': False,
                'error': 'Fornecedor não encontrado'
            }), 404
        
        conta_a_pagar = Payable(
            supplier_id=supplier.id,
            amount=data['amount'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date(),
            description=data.get('description', ''),
            status='pending'
        )
        
        db.session.add(conta_a_pagar)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': conta_a_pagar.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas_a_pagar/<int:id>/payment', methods=['POST'])
@login_required
def add_payment(id):
    """Adiciona um pagamento a uma conta"""
    try:
        data = request.get_json()
        conta_a_pagar = Payable.query.get_or_404(id)
        
        if conta_a_pagar.status == 'paid':
            return jsonify({
                'success': False,
                'error': 'Esta conta já está paga'
            }), 400
        
        payment = conta_a_pagar.add_payment(
            amount=data['amount'],
            payment_method=data['payment_method'],
            notes=data.get('notes')
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': conta_a_pagar.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas_a_pagar/supplier/<int:supplier_id>')
@login_required
def get_supplier_contas_a_pagar(supplier_id):
    """Retorna todas as contas a pagar de um fornecedor"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    contas_a_pagar = Payable.query.filter(
        Payable.supplier_id == supplier_id,
        Payable.status.in_(['pending', 'partial', 'overdue'])
    ).order_by(Payable.due_date).all()
    
    return jsonify({
        'success': True,
        'data': {
            'supplier': supplier.to_dict(),
            'contas_a_pagar': [conta_a_pagar.to_dict() for conta_a_pagar in contas_a_pagar]
        }
    })

@contas_a_pagar_bp.route('/api/contas_a_pagar/bulk-payment', methods=['POST'])
@login_required
def bulk_payment():
    """Processa o pagamento de múltiplas contas"""
    try:
        data = request.get_json()
        total_amount = float(data['amount'])
        payable_ids = data['payable_ids']
        payment_method = data['payment_method']
        
        # Ordena as contas por data de vencimento
        contas_a_pagar = Payable.query.filter(
            Payable.id.in_(payable_ids)
        ).order_by(Payable.due_date).all()
        
        if not contas_a_pagar:
            return jsonify({
                'success': False,
                'error': 'Nenhuma conta encontrada'
            }), 404
        
        # Processa o pagamento em ordem
        remaining_amount = total_amount
        payments = []
        
        for conta_a_pagar in contas_a_pagar:
            if remaining_amount <= 0:
                break
                
            # Determina o valor a ser pago nesta conta
            payment_amount = min(remaining_amount, float(conta_a_pagar.remaining_amount))
            
            # Registra o pagamento
            payment = conta_a_pagar.add_payment(
                amount=payment_amount,
                payment_method=payment_method,
                notes=f'Pagamento em lote - R$ {total_amount:.2f}'
            )
            
            payments.append(payment)
            db.session.add(payment)
            
            remaining_amount -= payment_amount
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'total_paid': total_amount - remaining_amount,
                'remaining_amount': remaining_amount,
                'contas_a_pagar': [conta_a_pagar.to_dict() for conta_a_pagar in contas_a_pagar]
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
