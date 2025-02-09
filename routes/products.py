from flask import Blueprint, request, jsonify, render_template, url_for, redirect
from flask_login import login_required, current_user
from models import db, Product, Category, Supplier, Invoice, InvoiceItem, Payable
from datetime import datetime
from decimal import Decimal

products_bp = Blueprint('products', __name__)

@products_bp.route('/products')
@login_required
def list_products():
    """Lista todos os produtos"""
    try:
        products = Product.query.all()
        categories = Category.query.order_by(Category.name).all()
        suppliers = Supplier.query.order_by(Supplier.name).all()
        return render_template('products/list.html', 
                             products=products,
                             categories=categories,
                             suppliers=suppliers)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products', methods=['GET'])
@login_required
def get_products():
    """Retorna todos os produtos com filtros opcionais"""
    try:
        query = Product.query

        # Filtro por categoria
        category_id = request.args.get('category_id')
        if category_id:
            query = query.filter(Product.category_id == category_id)

        # Filtro por fornecedor
        supplier_id = request.args.get('supplier_id')
        if supplier_id:
            query = query.filter(Product.supplier_id == supplier_id)

        # Filtro por status do estoque
        stock_status = request.args.get('stock_status')
        if stock_status == 'low':
            query = query.filter(Product.stock <= Product.min_stock)
        elif stock_status == 'normal':
            query = query.filter(Product.stock > Product.min_stock)

        # Filtro por busca (nome ou código)
        search = request.args.get('search')
        if search:
            search = f"%{search}%"
            query = query.filter(db.or_(
                Product.name.ilike(search),
                Product.code.ilike(search)
            ))

        # Ordenar por nome
        query = query.order_by(Product.name)

        # Executar a query
        products = query.all()

        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products/<int:id>', methods=['GET'])
@login_required
def get_product(id):
    """Retorna um produto específico"""
    try:
        product = Product.query.get_or_404(id)
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products', methods=['POST'])
@login_required
def create_product():
    """Cria um novo produto"""
    try:
        data = request.get_json()
        
        # Verifica se a categoria existe se foi fornecida
        category_id = data.get('category_id')
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                return jsonify({
                    'success': False,
                    'error': 'Categoria não encontrada'
                }), 404
        
        # Verifica se o fornecedor existe se foi fornecido
        supplier_id = data.get('supplier_id')
        if supplier_id:
            supplier = Supplier.query.get(supplier_id)
            if not supplier:
                return jsonify({
                    'success': False,
                    'error': 'Fornecedor não encontrado'
                }), 404
        
        # Converte a data de validade para datetime se fornecida
        expiry_date = data.get('expiry_date')
        if expiry_date:
            try:
                expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Data de validade inválida'
                }), 400

        # Calcula o preço de venda
        cost_price = float(data['cost_price'])
        markup = float(data['markup'])
        selling_price = cost_price * (1 + markup/100)

        product = Product(
            code=data['code'],
            name=data['name'],
            description=data.get('description', ''),
            category_id=category_id,
            supplier_id=supplier_id,
            cost_price=cost_price,
            markup=markup,
            selling_price=selling_price,
            stock=int(data['stock']),
            min_stock=int(data['min_stock']),
            expiry_date=expiry_date
        )
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': product.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/produtos', methods=['POST'])
@login_required
def create_product_api():
    """Cria um novo produto via API"""
    try:
        data = request.get_json()

        # Validação básica
        if not data.get('name') or not data.get('code'):
            return jsonify({
                'success': False,
                'error': 'Nome e código são obrigatórios'
            }), 400

        # Verifica se já existe um produto com o mesmo código
        existing_product = Product.query.filter_by(code=data.get('code')).first()
        if existing_product:
            return jsonify({
                'success': False,
                'error': 'Já existe um produto com este código'
            }), 400

        # Verifica se a categoria existe se foi fornecida
        category_id = data.get('category_id')
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                return jsonify({
                    'success': False,
                    'error': 'Categoria não encontrada'
                }), 404

        # Cria o novo produto
        product = Product(
            code=data.get('code'),
            name=data.get('name'),
            description=data.get('description', ''),
            cost_price=float(data.get('cost_price', 0)),
            markup=float(data.get('markup', 0)),
            selling_price=float(data.get('selling_price', 0)),
            stock=int(data.get('stock', 0)),
            min_stock=int(data.get('min_stock', 0)),
            max_stock=int(data.get('max_stock', 0)),
            unit=data.get('unit', 'UN'),
            category_id=category_id,
            status=data.get('status', 'active')
        )

        db.session.add(product)
        db.session.commit()

        return jsonify({
            'success': True,
            'product': product.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products/<int:id>', methods=['PUT'])
@login_required
def update_product(id):
    """Atualiza um produto"""
    try:
        data = request.get_json()
        product = Product.query.get_or_404(id)
        
        # Verifica se a categoria existe se foi fornecida
        category_id = data.get('category_id')
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                return jsonify({
                    'success': False,
                    'error': 'Categoria não encontrada'
                }), 404
        
        # Verifica se o fornecedor existe se foi fornecido
        supplier_id = data.get('supplier_id')
        if supplier_id:
            supplier = Supplier.query.get(supplier_id)
            if not supplier:
                return jsonify({
                    'success': False,
                    'error': 'Fornecedor não encontrado'
                }), 404
        
        # Atualiza os campos
        if 'code' in data:
            product.code = data['code']
        if 'name' in data:
            product.name = data['name']
        if 'description' in data:
            product.description = data.get('description', '')
        if 'category_id' in data:
            product.category_id = category_id
        if 'supplier_id' in data:
            product.supplier_id = supplier_id
        if 'cost_price' in data:
            product.cost_price = Decimal(str(data.get('cost_price', 0)))
        if 'markup' in data:
            product.markup = Decimal(str(data.get('markup', 0)))
        if 'selling_price' in data:
            product.selling_price = Decimal(str(data.get('selling_price', 0)))
        if 'stock' in data:
            product.stock = Decimal(str(data.get('stock', 0)))
        if 'min_stock' in data:
            product.min_stock = Decimal(str(data.get('min_stock', 0)))
        if 'max_stock' in data:
            product.max_stock = Decimal(str(data.get('max_stock', 0)))
        if 'unit' in data:
            product.unit = data.get('unit', 'un')
        if 'status' in data:
            product.status = data.get('status', 'active')
        if 'expiry_date' in data:
            expiry_date = data.get('expiry_date')
            if expiry_date:
                try:
                    product.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({
                        'success': False,
                        'error': 'Data de validade inválida'
                    }), 400
            else:
                product.expiry_date = None
        
        # Atualiza o preço de venda se necessário
        if 'cost_price' in data or 'markup' in data:
            product.update_selling_price()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products/<int:id>', methods=['DELETE'])
@login_required
def delete_product(id):
    """Exclui um produto"""
    try:
        product = Product.query.get_or_404(id)
        
        # Verifica se o produto tem movimentações
        if product.sale_items or product.invoice_items:
            return jsonify({
                'success': False,
                'error': 'Não é possível excluir um produto com movimentações'
            }), 400
        
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Produto excluído com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products/search')
@login_required
def search_products():
    """Pesquisa produtos por nome ou código de barras"""
    try:
        query = request.args.get('q', '')
        
        products = Product.query.filter(
            db.or_(
                Product.name.ilike(f'%{query}%'),
                Product.barcode.ilike(f'%{query}%')
            )
        ).all()
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/produtos/search')
@login_required
def search_products_api():
    """Busca produtos por código ou nome"""
    try:
        query = request.args.get('q', '')
        if len(query) < 3:
            return jsonify({
                'success': True,
                'products': []
            })

        # Busca por código ou nome
        products = Product.query.filter(
            (Product.code.ilike(f'%{query}%') | Product.name.ilike(f'%{query}%')) &
            (Product.status == 'active')
        ).limit(10).all()

        return jsonify({
            'success': True,
            'products': [{
                'id': p.id,
                'code': p.code,
                'name': p.name,
                'cost_price': float(p.cost_price) if p.cost_price else 0.00,
                'stock': float(p.stock) if p.stock else 0.00
            } for p in products]
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products/low-stock')
@login_required
def get_low_stock_products():
    """Retorna produtos com estoque baixo"""
    try:
        products = Product.query.filter(
            Product.stock <= Product.min_stock
        ).all()
        
        return jsonify({
            'success': True,
            'data': [product.to_dict() for product in products]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/products/add-invoice')
@login_required
def add_invoice():
    """Página para adicionar uma nova nota fiscal"""
    try:
        products = Product.query.filter_by(status='active').order_by(Product.name).all()
        suppliers = Supplier.query.order_by(Supplier.name).all()
        categories = Category.query.order_by(Category.name).all()
        return render_template('products/add_invoice.html',
                             products=products,
                             suppliers=suppliers,
                             categories=categories)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products/save-invoice', methods=['POST'])
@login_required
def save_invoice():
    """Salva uma nova nota fiscal com seus itens e gera conta a pagar"""
    try:
        # Início da transação
        db.session.begin_nested()

        # Dados da nota fiscal
        invoice_data = {
            'number': request.form['invoice_number'],
            'supplier_id': request.form['supplier_id'],
            'date': datetime.strptime(request.form['invoice_date'], '%Y-%m-%d').date(),
            'total': Decimal(request.form['total']),
            'status': request.form['status'],
            'payment_method': request.form['payment_method'],
            'payment_date': datetime.strptime(request.form['payment_date'], '%Y-%m-%d').date(),
            'notes': request.form.get('notes', '')
        }

        # Cria a nota fiscal
        invoice = Invoice(**invoice_data)
        db.session.add(invoice)
        db.session.flush()  # Para obter o ID da nota fiscal

        # Processa os itens da nota
        product_ids = request.form.getlist('product_ids[]')
        quantities = request.form.getlist('quantities[]')
        prices = request.form.getlist('prices[]')

        for i in range(len(product_ids)):
            if not product_ids[i]:
                continue
                
            quantity = Decimal(quantities[i])
            price = Decimal(prices[i])
            
            # Cria o item da nota
            item = InvoiceItem(
                invoice=invoice,
                product_id=product_ids[i],
                quantity=quantity,
                price=price,
                total=quantity * price
            )
            
            db.session.add(item)

            # Atualiza o estoque e preço do produto
            product = Product.query.get(product_ids[i])
            if product:
                product.stock += quantity
                product.cost_price = price
                product.update_selling_price()
        
        # Commit da transação
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Nota fiscal salva com sucesso!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/notas-fiscais', methods=['POST'])
@login_required
def save_invoice_api():
    """Salva uma nova nota fiscal com seus itens e gera conta a pagar via API"""
    try:
        data = request.get_json()
        
        if not data.get('invoice_number'):
            return jsonify({
                'success': False,
                'error': 'Número da nota fiscal é obrigatório'
            }), 400

        # Início da transação
        db.session.begin_nested()

        # Dados da nota fiscal
        invoice_data = {
            'number': data['invoice_number'],
            'supplier_id': data['supplier_id'],
            'date': datetime.strptime(data['invoice_date'], '%Y-%m-%d').date(),
            'payment_method': data['payment_method'],
            'payment_date': datetime.strptime(data['payment_date'], '%Y-%m-%d').date(),
            'status': data['status'],
            'notes': data.get('notes', '')
        }

        # Cria a nota fiscal
        invoice = Invoice(**invoice_data)
        db.session.add(invoice)
        db.session.flush()  # Para obter o ID da nota fiscal

        # Processa os itens da nota
        total = Decimal('0')
        for item in data['items']:
            quantity = Decimal(str(item['quantity']))
            price = Decimal(str(item['price']))
            item_total = quantity * price
            total += item_total
            
            # Cria o item da nota
            invoice_item = InvoiceItem(
                invoice_id=invoice.id,
                product_id=item['product_id'],
                quantity=quantity,
                price=price,
                total=item_total
            )
            db.session.add(invoice_item)

            # Atualiza o estoque e preço do produto
            product = Product.query.get(item['product_id'])
            if product:
                product.stock += quantity
                product.cost_price = price
                product.update_selling_price()

        # Atualiza o total da nota
        invoice.total = total

        # Cria a conta a pagar
        payable = Payable(
            supplier_id=invoice.supplier_id,
            invoice_id=invoice.id,
            amount=invoice.total,
            due_date=invoice.payment_date,
            status='paid' if invoice.status == 'paid' else 'pending',
            description=f'NF {invoice.number}',
            created_at=datetime.now()
        )
        db.session.add(payable)

        # Commit da transação
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Nota fiscal salva com sucesso!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/products/invoices')
@login_required
def list_invoices():
    """Lista todas as notas fiscais"""
    try:
        invoices = Invoice.query.order_by(Invoice.date.desc()).all()
        return render_template('products/invoices.html', invoices=invoices)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@products_bp.route('/api/products/invoice/<int:id>')
@login_required
def get_invoice(id):
    """Retorna os detalhes de uma nota fiscal específica"""
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
