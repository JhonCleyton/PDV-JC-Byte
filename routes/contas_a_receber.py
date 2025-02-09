from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Receivable, Customer
from datetime import datetime

contas_a_receber_bp = Blueprint('contas_a_receber', __name__)

@contas_a_receber_bp.route('/contas-a-receber')
@login_required
def list_receivables():
    """Lista todas as contas a receber"""
    try:
        receivables = Receivable.query.order_by(Receivable.due_date.asc()).all()
        return render_template('contas_a_receber/list.html', receivables=receivables)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas-a-receber', methods=['GET'])
@login_required
def get_receivables():
    """Retorna todas as contas a receber"""
    try:
        receivables = Receivable.query.order_by(Receivable.due_date.asc()).all()
        return jsonify({
            'success': True,
            'data': [receivable.to_dict() for receivable in receivables]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas-a-receber/<int:id>', methods=['GET'])
@login_required
def get_receivable(id):
    """Retorna uma conta a receber específica"""
    try:
        receivable = Receivable.query.get_or_404(id)
        return jsonify({
            'success': True,
            'data': receivable.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas-a-receber', methods=['POST'])
@login_required
def create_receivable():
    """Cria uma nova conta a receber"""
    try:
        data = request.get_json()
        
        # Verifica se o cliente existe
        customer = Customer.query.get(data['customer_id'])
        if not customer:
            return jsonify({
                'success': False,
                'error': 'Cliente não encontrado'
            }), 400
        
        receivable = Receivable(
            customer_id=data['customer_id'],
            description=data['description'],
            amount=data['amount'],
            due_date=datetime.strptime(data['due_date'], '%Y-%m-%d'),
            status=data.get('status', 'pendente'),
            payment_method=data.get('payment_method'),
            notes=data.get('notes')
        )
        
        db.session.add(receivable)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': receivable.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas-a-receber/<int:id>', methods=['PUT'])
@login_required
def update_receivable(id):
    """Atualiza uma conta a receber"""
    try:
        data = request.get_json()
        receivable = Receivable.query.get_or_404(id)
        
        # Não permite alterar contas pagas
        if receivable.status == 'pago':
            return jsonify({
                'success': False,
                'error': 'Não é possível alterar uma conta já paga'
            }), 400
        
        if 'description' in data:
            receivable.description = data['description']
        if 'amount' in data:
            receivable.amount = data['amount']
        if 'due_date' in data:
            receivable.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
        if 'status' in data:
            receivable.status = data['status']
            if data['status'] == 'pago':
                receivable.payment_date = datetime.now()
        if 'payment_method' in data:
            receivable.payment_method = data['payment_method']
        if 'notes' in data:
            receivable.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': receivable.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas-a-receber/<int:id>', methods=['DELETE'])
@login_required
def delete_receivable(id):
    """Exclui uma conta a receber"""
    try:
        receivable = Receivable.query.get_or_404(id)
        
        # Não permite excluir contas pagas
        if receivable.status == 'pago':
            return jsonify({
                'success': False,
                'error': 'Não é possível excluir uma conta já paga'
            }), 400
        
        db.session.delete(receivable)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Conta a receber excluída com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas-a-receber/vencidas', methods=['GET'])
@login_required
def get_overdue_receivables():
    """Retorna as contas a receber vencidas"""
    try:
        overdue = Receivable.query.filter(
            Receivable.status != 'pago',
            Receivable.due_date < datetime.now()
        ).order_by(Receivable.due_date.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [receivable.to_dict() for receivable in overdue]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas-a-receber/a-vencer', methods=['GET'])
@login_required
def get_upcoming_receivables():
    """Retorna as contas a receber a vencer nos próximos 30 dias"""
    try:
        today = datetime.now()
        upcoming = Receivable.query.filter(
            Receivable.status != 'pago',
            Receivable.due_date >= today,
            Receivable.due_date <= today + timedelta(days=30)
        ).order_by(Receivable.due_date.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [receivable.to_dict() for receivable in upcoming]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@contas_a_receber_bp.route('/api/contas-a-receber/por-cliente/<int:customer_id>', methods=['GET'])
@login_required
def get_customer_receivables(customer_id):
    """Retorna as contas a receber de um cliente específico"""
    try:
        receivables = Receivable.query.filter_by(
            customer_id=customer_id
        ).order_by(Receivable.due_date.asc()).all()
        
        return jsonify({
            'success': True,
            'data': [receivable.to_dict() for receivable in receivables]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
