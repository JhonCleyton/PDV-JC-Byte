from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime
import traceback

auth_bp = Blueprint('auth', __name__)

def init_admin():
    """Inicializa o usuário admin se não existir"""
    try:
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Criando usuário admin...")
            admin = User(
                name='Administrador',
                username='admin',
                role='admin',
                status='active'
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Usuário admin criado com sucesso.")
        else:
            print("Usuário admin já existe.")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar usuário admin: {str(e)}")
        raise

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login de usuário"""
    if request.method == 'GET':
        return render_template('login.html')
        
    try:
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
            remember = request.form.get('remember', False) == 'on'
        
        if not username or not password:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Usuário e senha são obrigatórios'
                }), 400
            else:
                flash('Usuário e senha são obrigatórios', 'danger')
                return redirect(url_for('auth.login'))
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Usuário ou senha inválidos'
                }), 401
            else:
                flash('Usuário ou senha inválidos', 'danger')
                return redirect(url_for('auth.login'))
            
        if user.status != 'active':
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Usuário inativo'
                }), 401
            else:
                flash('Usuário inativo', 'danger')
                return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        
        if request.is_json:
            return jsonify({
                'success': True,
                'data': user.to_dict()
            })
        else:
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        
    except Exception as e:
        traceback.print_exc()
        if request.is_json:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        else:
            flash('Erro ao realizar login', 'danger')
            return redirect(url_for('auth.login'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout de usuário"""
    try:
        logout_user()
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Logout realizado com sucesso'
            })
        else:
            flash('Logout realizado com sucesso!', 'success')
            return redirect(url_for('auth.login'))
    except Exception as e:
        traceback.print_exc()
        if request.is_json:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
        else:
            flash('Erro ao realizar logout', 'danger')
            return redirect(url_for('index'))

@auth_bp.route('/me')
@login_required
def me():
    """Retorna o usuário logado"""
    try:
        return jsonify({
            'success': True,
            'data': current_user.to_dict()
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/users', methods=['GET'])
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

@auth_bp.route('/users', methods=['POST'])
@login_required
def create_user():
    """Cria um novo usuário"""
    try:
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        # Validar campos obrigatórios
        if not username or not password:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Usuário e senha são obrigatórios'
                }), 400
            else:
                flash('Usuário e senha são obrigatórios', 'danger')
                return redirect(url_for('auth.create_user'))
            
        # Validar usuário único
        existing = User.query.filter_by(username=username).first()
        if existing:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Usuário já existe'
                }), 400
            else:
                flash('Usuário já existe', 'danger')
                return redirect(url_for('auth.create_user'))
        
        user = User(
            name=request.form.get('name'),
            username=username,
            role=request.form.get('role', 'operator'),
            status=request.form.get('status', 'active')
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'data': user.to_dict()
            })
        else:
            flash('Usuário criado com sucesso!', 'success')
            return redirect(url_for('index'))
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/users/<int:id>', methods=['PUT'])
@login_required
def update_user(id):
    """Atualiza um usuário"""
    try:
        user = User.query.get_or_404(id)
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        # Validar usuário único
        if username and username != user.username:
            existing = User.query.filter_by(username=username).first()
            if existing:
                if request.is_json:
                    return jsonify({
                        'success': False,
                        'error': 'Usuário já existe'
                    }), 400
                else:
                    flash('Usuário já existe', 'danger')
                    return redirect(url_for('auth.update_user', id=id))
        
        if request.form.get('name'):
            user.name = request.form.get('name')
        if username:
            user.username = username
        if password:
            user.set_password(password)
        if 'role' in request.form:
            user.role = request.form.get('role')
        if 'status' in request.form:
            user.status = request.form.get('status')
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'data': user.to_dict()
            })
        else:
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('index'))
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/users/<int:id>', methods=['DELETE'])
@login_required
def delete_user(id):
    """Exclui um usuário"""
    try:
        user = User.query.get_or_404(id)
        
        # Não permitir excluir o próprio usuário
        if user.username == 'admin':
            if request.is_json:
                return jsonify({
                    'success': False,
                    'error': 'Não é possível excluir o usuário admin'
                }), 400
            else:
                flash('Não é possível excluir o usuário admin', 'danger')
                return redirect(url_for('index'))
        
        db.session.delete(user)
        db.session.commit()
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Usuário excluído com sucesso'
            })
        else:
            flash('Usuário excluído com sucesso!', 'success')
            return redirect(url_for('index'))
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
