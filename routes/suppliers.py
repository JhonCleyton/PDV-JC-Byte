from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Supplier
from datetime import datetime

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/suppliers')
@login_required
def list_suppliers():
    """Lista todos os fornecedores"""
    try:
        suppliers = Supplier.query.all()
        return render_template('suppliers/list.html', suppliers=suppliers)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@suppliers_bp.route('/api/suppliers', methods=['GET'])
@login_required
def get_suppliers():
    """Retorna todos os fornecedores"""
    try:
        suppliers = Supplier.query.all()
        return jsonify({
            'success': True,
            'data': [supplier.to_dict() for supplier in suppliers]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@suppliers_bp.route('/api/suppliers/<int:id>', methods=['GET'])
@login_required
def get_supplier(id):
    """Retorna um fornecedor específico"""
    try:
        supplier = Supplier.query.get_or_404(id)
        return jsonify({
            'success': True,
            'data': supplier.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@suppliers_bp.route('/api/suppliers', methods=['POST'])
@login_required
def create_supplier():
    """Cria um novo fornecedor"""
    try:
        data = request.get_json()
        
        # Verifica se já existe um fornecedor com o mesmo CNPJ
        if data.get('cnpj'):
            existing = Supplier.query.filter_by(cnpj=data['cnpj']).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Já existe um fornecedor com este CNPJ'
                }), 400
        
        supplier = Supplier(
            name=data['name'],
            cnpj=data.get('cnpj'),
            email=data.get('email'),
            phone=data.get('phone'),
            contact_name=data.get('contact_name'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            payment_terms=data.get('payment_terms')
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': supplier.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@suppliers_bp.route('/api/fornecedores', methods=['POST'])
@login_required
def create_supplier_api():
    """Cria um novo fornecedor via API"""
    try:
        data = request.get_json()

        # Validação básica
        if not data.get('name'):
            return jsonify({
                'success': False,
                'error': 'Nome é obrigatório'
            }), 400

        supplier = Supplier(
            name=data.get('name'),
            cnpj=data.get('cnpj'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            contact_name=data.get('contact_name'),
            payment_terms=data.get('payment_terms')
        )

        db.session.add(supplier)
        db.session.commit()

        return jsonify({
            'success': True,
            'supplier': {
                'id': supplier.id,
                'name': supplier.name
            }
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@suppliers_bp.route('/api/suppliers/<int:id>', methods=['PUT'])
@login_required
def update_supplier(id):
    """Atualiza um fornecedor"""
    try:
        data = request.get_json()
        supplier = Supplier.query.get_or_404(id)
        
        # Verifica se o novo CNPJ já existe em outro fornecedor
        if 'cnpj' in data and data['cnpj'] != supplier.cnpj:
            existing = Supplier.query.filter_by(cnpj=data['cnpj']).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Já existe um fornecedor com este CNPJ'
                }), 400
        
        # Atualiza os campos
        if 'name' in data:
            supplier.name = data['name']
        if 'cnpj' in data:
            supplier.cnpj = data['cnpj']
        if 'email' in data:
            supplier.email = data['email']
        if 'phone' in data:
            supplier.phone = data['phone']
        if 'contact_name' in data:
            supplier.contact_name = data['contact_name']
        if 'address' in data:
            supplier.address = data['address']
        if 'city' in data:
            supplier.city = data['city']
        if 'state' in data:
            supplier.state = data['state']
        if 'zip_code' in data:
            supplier.zip_code = data['zip_code']
        if 'payment_terms' in data:
            supplier.payment_terms = data['payment_terms']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': supplier.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@suppliers_bp.route('/api/suppliers/<int:id>', methods=['DELETE'])
@login_required
def delete_supplier(id):
    """Exclui um fornecedor"""
    try:
        supplier = Supplier.query.get_or_404(id)
        
        # Verifica se o fornecedor tem notas fiscais ou contas a pagar
        if supplier.invoices or supplier.payables:
            return jsonify({
                'success': False,
                'error': 'Não é possível excluir um fornecedor que possui notas fiscais ou contas a pagar'
            }), 400
        
        db.session.delete(supplier)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Fornecedor excluído com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@suppliers_bp.route('/api/suppliers/search')
@login_required
def search_suppliers():
    """Pesquisa fornecedores por nome ou CNPJ"""
    try:
        query = request.args.get('q', '')
        
        suppliers = Supplier.query.filter(
            db.or_(
                Supplier.name.ilike(f'%{query}%'),
                Supplier.cnpj.ilike(f'%{query}%')
            )
        ).all()
        
        return jsonify({
            'success': True,
            'data': [supplier.to_dict() for supplier in suppliers]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
