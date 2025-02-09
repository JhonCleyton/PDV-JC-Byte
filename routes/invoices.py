from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Invoice, InvoiceItem, Supplier, Product, Payable
from datetime import datetime, date
from decimal import Decimal

nf_bp = Blueprint('nf', __name__)

@nf_bp.route('/nf/manage')
@login_required
def manage_nf():
    """Página de gerenciamento de notas fiscais"""
    return render_template('nf/manage.html')

@nf_bp.route('/api/nf/list')
@login_required
def list_nf():
    """Lista todas as notas fiscais com filtros"""
    supplier_id = request.args.get('supplier_id', type=int)
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Invoice.query
    
    if supplier_id:
        query = query.filter(Invoice.supplier_id == supplier_id)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
        query = query.filter(Invoice.date >= start)
    
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d').date()
        query = query.filter(Invoice.date <= end)
    
    invoices = query.order_by(Invoice.date.desc()).all()
    return jsonify({
        'success': True,
        'data': [invoice.to_dict() for invoice in invoices]
    })

@nf_bp.route('/api/nf', methods=['POST'])
@login_required
def create_nf():
    """Cria uma nova nota fiscal"""
    try:
        data = request.get_json()
        
        supplier = Supplier.query.get(data['supplier_id'])
        if not supplier:
            return jsonify({
                'success': False,
                'error': 'Fornecedor não encontrado'
            }), 404
        
        invoice = Invoice(
            supplier_id=supplier.id,
            number=data['number'],
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            total=0,
            status='pending'
        )
        
        db.session.add(invoice)
        
        # Processa os itens
        total = 0
        for item_data in data['items']:
            product = Product.query.get(item_data['product_id'])
            if not product:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Produto {item_data["product_id"]} não encontrado'
                }), 404
            
            item = InvoiceItem(
                invoice=invoice,
                product=product,
                quantity=float(item_data['quantity']),
                price=float(item_data['price'])
            )
            
            # Calcula o total do item
            item.total = Decimal(str(item.quantity)) * Decimal(str(item.price))
            total += float(item.total)
            
            # Atualiza o estoque e preço do produto
            product.stock += float(item.quantity)
            product.cost = float(item.price)
            product.update_price()  # Atualiza o preço de venda baseado na margem
            
            db.session.add(item)
        
        invoice.total = total
        
        # Cria a conta a pagar
        if data.get('create_payable'):
            payable = Payable(
                supplier_id=supplier.id,
                invoice_id=invoice.id,
                amount=total,
                due_date=datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data.get('due_date') else date.today(),
                description=f'NF {invoice.number}',
                status='pending'
            )
            db.session.add(payable)
        
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

@nf_bp.route('/api/nf/<int:id>', methods=['PUT'])
@login_required
def update_nf(id):
    """Atualiza uma nota fiscal"""
    try:
        data = request.get_json()
        invoice = Invoice.query.get_or_404(id)
        
        if invoice.status != 'pending':
            return jsonify({
                'success': False,
                'error': 'Apenas notas fiscais pendentes podem ser alteradas'
            }), 400
        
        # Atualiza os campos básicos
        invoice.number = data.get('number', invoice.number)
        invoice.date = datetime.strptime(data['date'], '%Y-%m-%d').date() if data.get('date') else invoice.date
        
        # Se houver novos itens, remove os antigos e adiciona os novos
        if 'items' in data:
            # Reverte as alterações de estoque
            for item in invoice.items:
                item.product.stock -= float(item.quantity)
                db.session.delete(item)
            
            # Adiciona os novos itens
            total = 0
            for item_data in data['items']:
                product = Product.query.get(item_data['product_id'])
                if not product:
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'error': f'Produto {item_data["product_id"]} não encontrado'
                    }), 404
                
                item = InvoiceItem(
                    invoice=invoice,
                    product=product,
                    quantity=float(item_data['quantity']),
                    price=float(item_data['price'])
                )
                
                # Calcula o total do item
                item.total = Decimal(str(item.quantity)) * Decimal(str(item.price))
                total += float(item.total)
                
                # Atualiza o estoque e preço do produto
                product.stock += float(item.quantity)
                product.cost = float(item.price)
                product.update_price()
                
                db.session.add(item)
            
            invoice.total = total
            
            # Atualiza a conta a pagar se existir
            if invoice.payable:
                invoice.payable.amount = total
        
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

@nf_bp.route('/api/nf/<int:id>', methods=['DELETE'])
@login_required
def delete_nf(id):
    """Exclui uma nota fiscal"""
    try:
        invoice = Invoice.query.get_or_404(id)
        
        if invoice.status != 'pending':
            return jsonify({
                'success': False,
                'error': 'Apenas notas fiscais pendentes podem ser excluídas'
            }), 400
        
        # Reverte as alterações de estoque
        for item in invoice.items:
            item.product.stock -= float(item.quantity)
            db.session.delete(item)
        
        # Exclui a conta a pagar se existir e não tiver pagamentos
        if invoice.payable and not invoice.payable.payments:
            db.session.delete(invoice.payable)
        
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

@nf_bp.route('/api/nf/<int:id>/confirm', methods=['POST'])
@login_required
def confirm_nf(id):
    """Confirma uma nota fiscal"""
    try:
        invoice = Invoice.query.get_or_404(id)
        
        if invoice.status != 'pending':
            return jsonify({
                'success': False,
                'error': 'Esta nota fiscal não está pendente'
            }), 400
        
        invoice.status = 'confirmed'
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
