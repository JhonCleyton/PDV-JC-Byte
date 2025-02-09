from models import db, Payable
from app import app

STATUS_MAP = {
    'pendente': 'pending',
    'pago': 'paid',
    'vencido': 'overdue',
    'parcial': 'partial'
}

with app.app_context():
    payables = Payable.query.all()
    print('\nAtualizando status das contas a pagar...')
    for p in payables:
        old_status = p.status
        if old_status in STATUS_MAP:
            p.status = STATUS_MAP[old_status]
            print(f'ID {p.id}: {old_status} -> {p.status}')
    
    db.session.commit()
    print('\nAtualização concluída!')
