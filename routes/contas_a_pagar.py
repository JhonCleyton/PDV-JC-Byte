from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Payable, Supplier
from datetime import datetime, timedelta

contas_a_pagar_bp = Blueprint('contas_a_pagar', __name__)

@contas_a_pagar_bp.route('/contas-a-pagar')
@login_required
def list_payables():
    """Lista todas as contas a pagar"""
    try:
        payables = Payable.query.order_by(Payable.due_date.asc()).all()
        
        # Atualiza o status de todas as contas
        for payable in payables:
            payable.update_status()
        db.session.commit()
        
        return render_template('contas_a_pagar/list.html', payables=payables)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas-a-pagar', methods=['GET'])
@login_required
def get_payables():
    """Retorna todas as contas a pagar"""
    try:
        payables = Payable.query.order_by(Payable.due_date.asc()).all()
        return jsonify({
            'success': True,
            'data': [payable.to_dict() for payable in payables]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas-a-pagar/<int:id>', methods=['GET'])
@login_required
def get_payable(id):
    """Retorna uma conta a pagar específica"""
    try:
        payable = Payable.query.get_or_404(id)
        return jsonify({
            'success': True,
            'data': payable.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas-a-pagar', methods=['POST'])
@login_required
def create_payable():
    """Cria uma nova conta a pagar"""
    try:
        data = request.get_json()
        
        # Verifica se o fornecedor existe
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({
                'success': False,
                'error': 'Fornecedor não encontrado'
            }), 400
        
        payable = Payable(
            supplier_id=data['supplier_id'],
            description=data['description'],
            amount=data['amount'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d'),
            status=data.get('status', 'pending'),  # Status padrão em inglês
            payment_method=data.get('payment_method'),
            notes=data.get('notes')
        )
        
        db.session.add(payable)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': payable.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas-a-pagar/<int:id>', methods=['PUT'])
@login_required
def update_payable(id):
    """Atualiza uma conta a pagar"""
    try:
        data = request.get_json()
        payable = Payable.query.get_or_404(id)
        
        # Atualiza os campos
        if 'description' in data:
            payable.description = data['description']
        if 'amount' in data:
            payable.amount = data['amount']
        if 'due_date' in data:
            payable.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        if 'status' in data:
            if data['status'] == 'paid':  # Agora verifica o status em inglês
                # Se estiver marcando como pago, atualiza o valor pago
                payable.paid_amount = payable.amount
            else:
                # Se estiver mudando para outro status, zera o valor pago
                payable.paid_amount = 0
            payable.status = data['status']  # Define o status diretamente
            payable.update_remaining_amount()  # Atualiza o valor restante
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': payable.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas-a-pagar/<int:id>', methods=['DELETE'])
@login_required
def delete_payable(id):
    """Exclui uma conta a pagar"""
    try:
        payable = Payable.query.get_or_404(id)
        
        # Não permite excluir contas pagas
        if payable.status == 'paid':  # Atualizado para inglês
            return jsonify({
                'success': False,
                'error': 'Não é possível excluir uma conta já paga'
            }), 400
        
        db.session.delete(payable)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Conta a pagar excluída com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas-a-pagar/vencidas', methods=['GET'])
@login_required
def get_overdue_payables():
    """Retorna as contas a pagar vencidas"""
    try:
        overdue = Payable.query.filter(
            Payable.status != 'paid',
            Payable.due_date < datetime.now()
        ).order_by(Payable.due_date.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [payable.to_dict() for payable in overdue]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas-a-pagar/a-vencer', methods=['GET'])
@login_required
def get_upcoming_payables():
    """Retorna as contas a pagar a vencer nos próximos 30 dias"""
    try:
        today = datetime.now()
        upcoming = Payable.query.filter(
            Payable.status != 'paid',
            Payable.due_date >= today,
            Payable.due_date <= today + timedelta(days=30)
        ).order_by(Payable.due_date.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [payable.to_dict() for payable in upcoming]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_pagar_bp.route('/api/contas-a-pagar/por-fornecedor/<int:supplier_id>', methods=['GET'])
@login_required
def get_supplier_payables(supplier_id):
    """Retorna as contas a pagar de um fornecedor específico"""
    try:
        payables = Payable.query.filter_by(
            supplier_id=supplier_id
        ).order_by(Payable.due_date.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [payable.to_dict() for payable in payables]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
