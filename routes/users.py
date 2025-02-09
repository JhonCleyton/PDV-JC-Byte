from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db, User
from datetime import datetime
from werkzeug.security import generate_password_hash

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
def list_users():
    """Lista todos os usuários"""
    try:
        users = User.query.all()
        return render_template('users/list.html', users=users)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_bp.route('/api/users', methods=['GET'])
@login_required
def get_users():
    """Retorna todos os usuários"""
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_bp.route('/api/users/<int:id>', methods=['GET'])
@login_required
def get_user(id):
    """Retorna um usuário específico"""
    try:
        user = User.query.get_or_404(id)
        return jsonify({
            'success': True,
            'data': user.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_bp.route('/api/users', methods=['POST'])
@login_required
def create_user():
    """Cria um novo usuário"""
    try:
        data = request.get_json()
        
        # Verifica se já existe um usuário com o mesmo username
        if User.query.filter_by(username=data['username']).first():
            return jsonify({
                'success': False,
                'error': 'Nome de usuário já cadastrado'
            }), 400
        
        user = User(
            name=data['name'],
            username=data['username'],
            password=generate_password_hash(data['password']),
            role=data.get('role', 'cashier'),
            status=data.get('status', 'active')
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_bp.route('/api/users/<int:id>', methods=['PUT'])
@login_required
def update_user(id):
    """Atualiza um usuário"""
    try:
        data = request.get_json()
        user = User.query.get_or_404(id)
        
        # Apenas administradores podem alterar outros usuários
        if current_user.id != user.id and current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Permissão negada'
            }), 403
        
        # Verifica se o novo email já existe
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({
                    'success': False,
                    'error': 'Email já cadastrado'
                }), 400
            user.email = data['email']
        
        if 'name' in data:
            user.name = data['name']
        if 'password' in data:
            user.password = generate_password_hash(data['password'])
        if 'role' in data and current_user.role == 'admin':
            user.role = data['role']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_bp.route('/api/users/<int:id>', methods=['DELETE'])
@login_required
def delete_user(id):
    """Exclui um usuário"""
    try:
        # Apenas administradores podem excluir usuários
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Permissão negada'
            }), 403
        
        user = User.query.get_or_404(id)
        
        # Não permite excluir o próprio usuário
        if user.id == current_user.id:
            return jsonify({
                'success': False,
                'error': 'Não é possível excluir o próprio usuário'
            }), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuário excluído com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_bp.route('/api/users/profile', methods=['GET'])
@login_required
def get_profile():
    """Retorna o perfil do usuário atual"""
    try:
        return jsonify({
            'success': True,
            'data': current_user.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@users_bp.route('/api/users/profile', methods=['PUT'])
@login_required
def update_profile():
    """Atualiza o perfil do usuário atual"""
    try:
        data = request.get_json()
        
        # Verifica se o novo email já existe
        if 'email' in data and data['email'] != current_user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({
                    'success': False,
                    'error': 'Email já cadastrado'
                }), 400
            current_user.email = data['email']
        
        if 'name' in data:
            current_user.name = data['name']
        if 'password' in data:
            current_user.password = generate_password_hash(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': current_user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
