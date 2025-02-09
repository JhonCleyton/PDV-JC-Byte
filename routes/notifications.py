from flask import Blueprint, request, jsonify
from flask_login import login_required
from models import db, Notification
from datetime import datetime, timedelta

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Retorna todas as notificações, ordenadas por data e status de leitura"""
    try:
        # Primeiro as não lidas, depois as lidas, ordenadas por data
        notifications = Notification.query.order_by(
            Notification.read.asc(),
            Notification.created_at.desc()
        ).limit(50).all()  # Limitando a 50 notificações para performance
        
        return jsonify({
            'success': True,
            'data': [notification.to_dict() for notification in notifications]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/notifications/<int:id>/read', methods=['POST'])
@login_required
def mark_as_read(id):
    """Marca uma notificação como lida"""
    try:
        notification = Notification.query.get_or_404(id)
        notification.read = True
        notification.read_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': notification.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/notifications/read-all', methods=['POST'])
@login_required
def mark_all_as_read():
    """Marca todas as notificações como lidas"""
    try:
        notifications = Notification.query.filter_by(read=False).all()
        current_time = datetime.now()
        
        for notification in notifications:
            notification.read = True
            notification.read_at = current_time
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Todas as notificações foram marcadas como lidas'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/notifications/unread-count', methods=['GET'])
@login_required
def get_unread_count():
    """Retorna o número de notificações não lidas"""
    try:
        count = Notification.query.filter_by(read=False).count()
        return jsonify({
            'success': True,
            'data': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@notifications_bp.route('/api/notifications/clear-old', methods=['POST'])
@login_required
def clear_old_notifications():
    """Remove notificações lidas com mais de 30 dias"""
    try:
        thirty_days_ago = datetime.now() - timedelta(days=30)
        old_notifications = Notification.query.filter(
            Notification.read == True,
            Notification.read_at <= thirty_days_ago
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Removidas {old_notifications} notificações antigas'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
