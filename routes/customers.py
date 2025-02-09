from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from models import db, Customer, Sale, SaleItem, Receivable
import traceback

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/api/clientes', methods=['GET'])
@login_required
def get_customers():
    """Retorna todos os clientes"""
    try:
        print("Buscando todos os clientes")
        customers = Customer.query.all()
        print(f"Clientes encontrados: {len(customers)}")
        return jsonify({
            'success': True,
            'data': [customer.to_dict() for customer in customers]
        })
    except Exception as e:
        print(f"Erro ao buscar clientes: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/api/clientes/<int:id>', methods=['GET'])
@login_required
def get_customer(id):
    """Retorna um cliente específico"""
    try:
        print(f"Buscando cliente com ID: {id}")
        customer = Customer.query.get_or_404(id)
        print(f"Cliente encontrado: {customer}")
        return jsonify({
            'success': True,
            'data': customer.to_dict()
        })
    except Exception as e:
        print(f"Erro ao buscar cliente: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/api/clientes', methods=['POST'])
@login_required
def create_customer():
    """Cria um novo cliente"""
    try:
        print("Criando novo cliente")
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data.get('name'):
            print("Erro: nome é obrigatório")
            return jsonify({
                'success': False,
                'error': 'Nome é obrigatório'
            }), 400
            
        # Validar CPF único
        if data.get('cpf'):
            existing = Customer.query.filter_by(cpf=data['cpf']).first()
            if existing:
                print("Erro: CPF já cadastrado")
                return jsonify({
                    'success': False,
                    'error': 'CPF já cadastrado'
                }), 400
        
        # Criar o cliente (a matrícula será gerada automaticamente)
        customer = Customer(
            name=data['name'],
            cpf=data.get('cpf'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            credit_limit=data.get('credit_limit', 0),
            status=data.get('status', 'active')
        )
        
        db.session.add(customer)
        db.session.commit()
        
        print(f"Cliente criado com sucesso: {customer}")
        return jsonify({
            'success': True,
            'data': customer.to_dict()
        })
        
    except Exception as e:
        print(f"Erro ao criar cliente: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/api/clientes/<int:id>', methods=['PUT'])
@login_required
def update_customer(id):
    """Atualiza um cliente"""
    try:
        print(f"Atualizando cliente com ID: {id}")
        customer = Customer.query.get_or_404(id)
        data = request.get_json()
        
        # Validar campos obrigatórios
        if not data.get('name'):
            print("Erro: nome é obrigatório")
            return jsonify({
                'success': False,
                'error': 'Nome é obrigatório'
            }), 400
            
        # Validar CPF único
        if data.get('cpf') and data['cpf'] != customer.cpf:
            existing = Customer.query.filter_by(cpf=data['cpf']).first()
            if existing:
                print("Erro: CPF já cadastrado")
                return jsonify({
                    'success': False,
                    'error': 'CPF já cadastrado'
                }), 400
        
        customer.name = data['name']
        customer.cpf = data.get('cpf')
        customer.email = data.get('email')
        customer.phone = data.get('phone')
        customer.address = data.get('address')
        customer.credit_limit = data.get('credit_limit', customer.credit_limit)
        customer.status = data.get('status', customer.status)
        
        db.session.commit()
        
        print(f"Cliente atualizado com sucesso: {customer}")
        return jsonify({
            'success': True,
            'data': customer.to_dict()
        })
        
    except Exception as e:
        print(f"Erro ao atualizar cliente: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/api/clientes/<int:id>', methods=['DELETE'])
@login_required
def delete_customer(id):
    """Exclui um cliente"""
    try:
        print(f"Excluindo cliente com ID: {id}")
        customer = Customer.query.get_or_404(id)
        
        # Verificar se o cliente tem vendas ou contas a receber
        if customer.sales or customer.receivables:
            print("Erro: cliente possui vendas ou contas a receber")
            return jsonify({
                'success': False,
                'error': 'Cliente possui vendas ou contas a receber'
            }), 400
        
        db.session.delete(customer)
        db.session.commit()
        
        print(f"Cliente excluído com sucesso: {customer}")
        return jsonify({
            'success': True,
            'message': 'Cliente excluído com sucesso'
        })
        
    except Exception as e:
        print(f"Erro ao excluir cliente: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/api/clientes/<int:id>/sales', methods=['GET'])
@login_required
def get_customer_sales(id):
    """Retorna o histórico de vendas e contas a receber do cliente"""
    try:
        print(f"Buscando histórico de vendas do cliente com ID: {id}")
        customer = Customer.query.get_or_404(id)
        
        # Buscar vendas
        sales = Sale.query.filter_by(customer_id=id).order_by(Sale.date.desc()).all()
        print(f"Vendas encontradas: {len(sales)}")
        
        # Buscar contas a receber
        receivables = Receivable.query.filter_by(customer_id=id).order_by(Receivable.due_date.desc()).all()
        print(f"Contas a receber encontradas: {len(receivables)}")
        
        return jsonify({
            'success': True,
            'data': {
                'sales': [sale.to_dict() for sale in sales],
                'receivables': [receivable.to_dict() for receivable in receivables]
            }
        })
        
    except Exception as e:
        print(f"Erro ao buscar histórico de vendas: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/api/clientes/<int:id>/receivables', methods=['GET'])
@login_required
def get_customer_receivables(id):
    """Retorna as contas a receber do cliente"""
    try:
        print(f"Buscando contas a receber do cliente com ID: {id}")
        customer = Customer.query.get_or_404(id)
        receivables = Receivable.query.filter_by(customer_id=id).order_by(Receivable.due_date.desc()).all()
        
        print(f"Contas a receber encontradas: {len(receivables)}")
        return jsonify({
            'success': True,
            'data': [receivable.to_dict() for receivable in receivables]
        })
        
    except Exception as e:
        print(f"Erro ao buscar contas a receber: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/api/receivables/<int:id>/pay', methods=['POST'])
@login_required
def pay_receivable(id):
    """Registra o pagamento de uma conta a receber"""
    try:
        print(f"Registrando pagamento da conta a receber com ID: {id}")
        receivable = Receivable.query.get_or_404(id)
        
        if receivable.status == 'paid':
            print("Erro: conta já está paga")
            return jsonify({
                'success': False,
                'error': 'Conta já está paga'
            }), 400
        
        receivable.status = 'paid'
        receivable.customer.update_debt()
        
        db.session.commit()
        
        print(f"Pagamento registrado com sucesso: {receivable}")
        return jsonify({
            'success': True,
            'data': receivable.to_dict()
        })
        
    except Exception as e:
        print(f"Erro ao registrar pagamento: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/api/clientes/active', methods=['GET'])
@login_required
def get_active_customers():
    """Retorna o número de clientes ativos"""
    try:
        print("Buscando clientes ativos")
        count = Customer.query.filter_by(status='active').count()
        print(f"Clientes ativos encontrados: {count}")
        return jsonify({
            'success': True,
            'data': {
                'count': count
            }
        })
    except Exception as e:
        print(f"Erro ao buscar clientes ativos: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/buscar/<registration>')
@login_required
def get_customer_by_registration(registration):
    """Retorna um cliente pela matrícula ou CPF"""
    try:
        print(f"\n=== Buscando cliente ===")
        print(f"Registro original: {registration}")
        
        # Remove caracteres não numéricos
        registration = ''.join(filter(str.isdigit, registration))
        print(f"Registro limpo: {registration}")
        
        # Primeiro tenta buscar por matrícula
        print("\nTentando buscar por matrícula...")
        customer = Customer.query.filter(
            Customer.registration == registration
        ).first()
        
        if customer:
            print(f"Cliente encontrado por matrícula: {customer.name}")
        else:
            print("Cliente não encontrado por matrícula")
            
            # Tenta buscar por CPF
            print("\nTentando buscar por CPF...")
            customer = Customer.query.filter(
                Customer.cpf == registration
            ).first()
            
            if customer:
                print(f"Cliente encontrado por CPF: {customer.name}")
            else:
                print("Cliente não encontrado por CPF")
        
        if customer:
            print("\nDados do cliente:")
            print(f"- ID: {customer.id}")
            print(f"- Nome: {customer.name}")
            print(f"- CPF: {customer.cpf}")
            print(f"- Matrícula: {customer.registration}")
            
            try:
                customer_dict = customer.to_dict()
                if customer_dict is None:
                    raise ValueError("Erro ao converter cliente para dicionário")
                    
                print(f"- Dict: {customer_dict}")
                return jsonify({
                    'success': True,
                    'customer': customer_dict
                })
            except Exception as e:
                print(f"Erro ao converter cliente para dict: {e}")
                traceback.print_exc()
                return jsonify({
                    'success': False,
                    'error': 'Erro ao processar dados do cliente'
                }), 500
        
        print("\nCliente não encontrado")
        return jsonify({
            'success': False,
            'error': 'Cliente não encontrado'
        }), 404
            
    except Exception as e:
        print(f"\n=== ERRO ao buscar cliente ===")
        print(f"Tipo do erro: {type(e)}")
        print(f"Erro: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@customers_bp.route('/api/clientes/<int:id>/dividas', methods=['GET'])
@login_required
def get_customer_debts(id):
    """Retorna todas as dívidas pendentes ou parcialmente pagas do cliente"""
    try:
        print(f"Buscando dívidas do cliente com ID: {id}")
        customer = Customer.query.get_or_404(id)
        
        # Buscar contas a receber pendentes ou parcialmente pagas
        dividas = Receivable.query.filter(
            Receivable.customer_id == id,
            Receivable.status.in_(['pending', 'partial', 'overdue']),
            Receivable.remaining_amount > 0  # Garante que ainda há valor a receber
        ).order_by(Receivable.due_date.desc()).all()
        
        print(f"Dívidas encontradas: {len(dividas)}")
        return jsonify({
            'success': True,
            'dividas': [divida.to_dict() for divida in dividas]
        })
        
    except Exception as e:
        print(f"Erro ao buscar dívidas: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
