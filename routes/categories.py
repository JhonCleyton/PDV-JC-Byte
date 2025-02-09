from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Category
from datetime import datetime

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories')
@login_required
def list_categories():
    """Lista todas as categorias"""
    try:
        categories = Category.query.all()
        return render_template('categories/list.html', categories=categories)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/api/categories', methods=['GET'])
@login_required
def get_categories():
    """Retorna todas as categorias"""
    try:
        categories = Category.query.all()
        return jsonify({
            'success': True,
            'data': [category.to_dict() for category in categories]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/api/categories/<int:id>', methods=['GET'])
@login_required
def get_category(id):
    """Retorna uma categoria específica"""
    try:
        category = Category.query.get_or_404(id)
        return jsonify({
            'success': True,
            'data': category.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/api/categories', methods=['POST'])
@login_required
def create_category():
    """Cria uma nova categoria"""
    try:
        data = request.get_json()
        
        # Verifica se já existe uma categoria com o mesmo nome
        existing = Category.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({
                'success': False,
                'error': 'Já existe uma categoria com este nome'
            }), 400
        
        category = Category(
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': category.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/api/categories/<int:id>', methods=['PUT'])
@login_required
def update_category(id):
    """Atualiza uma categoria"""
    try:
        data = request.get_json()
        category = Category.query.get_or_404(id)
        
        # Verifica se o novo nome já existe em outra categoria
        if 'name' in data and data['name'] != category.name:
            existing = Category.query.filter_by(name=data['name']).first()
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'Já existe uma categoria com este nome'
                }), 400
            category.name = data['name']
        
        if 'description' in data:
            category.description = data['description']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': category.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@categories_bp.route('/api/categories/<int:id>', methods=['DELETE'])
@login_required
def delete_category(id):
    """Exclui uma categoria"""
    try:
        category = Category.query.get_or_404(id)
        
        # Verifica se existem produtos nesta categoria
        if category.products:
            return jsonify({
                'success': False,
                'error': 'Não é possível excluir uma categoria que possui produtos'
            }), 400
        
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Categoria excluída com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
