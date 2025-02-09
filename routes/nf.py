from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Invoice, Supplier, InvoiceItem, Product, Payable
from datetime import datetime

nf_bp = Blueprint('nf', __name__)

@nf_bp.route('/notas-fiscais')
@login_required
def list_invoices():
    """Lista todas as notas fiscais"""
    try:
        invoices = Invoice.query.order_by(Invoice.date.desc()).all()
        return render_template('nf/list.html', invoices=invoices)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@nf_bp.route('/api/notas-fiscais', methods=['GET'])
@login_required
def get_invoices():
    """Retorna todas as notas fiscais"""
    try:
        invoices = Invoice.query.order_by(Invoice.date.desc()).all()
        return jsonify({
            'success': True,
            'data': [invoice.to_dict() for invoice in invoices]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@nf_bp.route('/api/notas-fiscais/<int:id>', methods=['GET'])
@login_required
def get_invoice(id):
    """Retorna uma nota fiscal específica"""
    try:
        invoice = Invoice.query.get_or_404(id)
        return jsonify({
            'success': True,
            'data': invoice.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@nf_bp.route('/api/notas-fiscais', methods=['POST'])
@login_required
def create_invoice():
    """Cria uma nova nota fiscal"""
    try:
        data = request.get_json()
        
        # Verifica se o fornecedor existe
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({
                'success': False,
                'error': 'Fornecedor não encontrado'
            }), 400
        
        # Verifica se já existe uma nota fiscal com o mesmo número
        existing = Invoice.query.filter_by(number=data['invoice_number']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Já existe uma nota fiscal com este número'
            }), 400
        
        # Calcula o total da nota
        total = sum(item['quantity'] * item['price'] for item in data['items'])
        
        # Cria a nota fiscal
        invoice = Invoice(
            supplier_id=data['supplier_id'],
            number=data['invoice_number'],
            date=datetime.strptime(data['invoice_date'], '%Y-%m-%d'),
            payment_date=datetime.strptime(data['payment_date'], '%Y-%m-%d'),
            payment_method=data['payment_method'],
            status=data['status'],
            total=total,
            notes=data.get('notes', '')
        )
        
        db.session.add(invoice)
        db.session.flush()  # Para obter o ID da nota fiscal
        
        # Processa os itens da nota
        for item in data['items']:
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item['product_id'],
                quantity=item['quantity'],
                price=item['price'],
                total=item['quantity'] * item['price']
            )
            db.session.add(invoice_item)
            
            # Atualiza o estoque e preço do produto
            product = Product.query.get(item['product_id'])
            if product:
                product.stock += item['quantity']
                product.cost_price = item['price']
                product.update_selling_price()  # Corrigido o nome do método
        
        # Se a nota estiver pendente, cria uma conta a pagar
        if invoice.status == 'pending':
            payable = Payable(
                supplier_id=invoice.supplier_id,
                invoice_id=invoice.id,
                amount=invoice.total,
                due_date=invoice.payment_date,
                status='pending',
                description=f'NF {invoice.number}',
                created_at=datetime.now()
            )
            db.session.add(payable)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Nota fiscal salva com sucesso!',
            'data': invoice.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@nf_bp.route('/api/notas-fiscais/<int:id>', methods=['PUT'])
@login_required
def update_invoice(id):
    """Atualiza uma nota fiscal"""
    try:
        data = request.get_json()
        invoice = Invoice.query.get_or_404(id)
        
        # Não permite alterar notas fiscais pagas
        if invoice.status == 'pago':
            return jsonify({
                'success': False,
                'error': 'Não é possível alterar uma nota fiscal já paga'
            }), 400
        
        # Verifica se o novo número já existe em outra nota fiscal
        if 'number' in data and data['number'] != invoice.number:
            existing = Invoice.query.filter_by(number=data['number']).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Já existe uma nota fiscal com este número'
                }), 400
            invoice.number = data['number']
        
        if 'series' in data:
            invoice.series = data['series']
        if 'date' in data:
            invoice.date = datetime.strptime(data['date'], '%Y-%m-%d')
        if 'total' in data:
            invoice.total = data['total']
        if 'tax' in data:
            invoice.tax = data['tax']
        if 'status' in data:
            invoice.status = data['status']
            if data['status'] == 'pago':
                invoice.payment_date = datetime.now()
        if 'payment_method' in data:
            invoice.payment_method = data['payment_method']
        if 'notes' in data:
            invoice.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': invoice.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@nf_bp.route('/api/notas-fiscais/<int:id>', methods=['DELETE'])
@login_required
def delete_invoice(id):
    """Exclui uma nota fiscal"""
    try:
        invoice = Invoice.query.get_or_404(id)
        
        # Não permite excluir notas fiscais pagas
        if invoice.status == 'pago':
            return jsonify({
                'success': False,
                'error': 'Não é possível excluir uma nota fiscal já paga'
            }), 400
        
        db.session.delete(invoice)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Nota fiscal excluída com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@nf_bp.route('/api/notas-fiscais/por-fornecedor/<int:supplier_id>', methods=['GET'])
@login_required
def get_supplier_invoices(supplier_id):
    """Retorna as notas fiscais de um fornecedor específico"""
    try:
        invoices = Invoice.query.filter_by(
            supplier_id=supplier_id
        ).order_by(Invoice.date.desc()).all()
        
        return jsonify({
            'success': True,
            'data': [invoice.to_dict() for invoice in invoices]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@nf_bp.route('/api/notas-fiscais/por-periodo', methods=['GET'])
@login_required
def get_invoices_by_period():
    """Retorna as notas fiscais de um período específico"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Invoice.query
        
        if start_date:
            query = query.filter(Invoice.date >= start_date)
        if end_date:
            query = query.filter(Invoice.date <= end_date)
        
        invoices = query.order_by(Invoice.date.desc()).all()
        
        total = sum(invoice.total for invoice in invoices)
        tax_total = sum(invoice.tax for invoice in invoices)
        
        return jsonify({
            'success': True,
            'data': {
                'invoices': [invoice.to_dict() for invoice in invoices],
                'total': total,
                'tax_total': tax_total,
                'count': len(invoices)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
