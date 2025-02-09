from flask import Blueprint, jsonify, render_template
from flask_login import login_required
from models import db, Sale, Customer, Product, Receivable, Payable, SaleItem
from datetime import datetime, date, timedelta
from sqlalchemy import func
import traceback

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/api/dashboard/today')
@login_required
def get_today_stats():
    """Retorna as estatísticas do dia"""
    try:
        print("\n=== Obtendo estatísticas do dashboard ===")
        today = date.today()
        
        # Vendas do dia
        total_sales = 0
        sales = Sale.query.filter(
            func.date(Sale.date) == today
        ).all()
        for sale in sales:
            total_sales += float(sale.total or 0)
        print(f"Total de vendas do dia: R$ {total_sales:.2f}")
        
        # Vendas dos últimos 7 dias
        seven_days_ago = today - timedelta(days=7)
        total_last_7_days = 0
        sales_7_days = Sale.query.filter(
            func.date(Sale.date) >= seven_days_ago,
            func.date(Sale.date) <= today
        ).all()
        for sale in sales_7_days:
            total_last_7_days += float(sale.total or 0)
        print(f"Total de vendas (7 dias): R$ {total_last_7_days:.2f}")
        
        # Clientes ativos
        active_customers = Customer.query.filter_by(status='active').count()
        print(f"Clientes ativos: {active_customers}")
        
        # Produtos em baixa
        low_stock = Product.query.filter(Product.stock <= Product.min_stock).count()
        print(f"Produtos em baixa: {low_stock}")
        
        # Total a receber
        total_receivables = 0
        total_received = 0
        total_pending = 0
        total_overdue = 0
        receivables = Receivable.query.filter(
            Receivable.status.in_(['pending', 'partial', 'overdue'])
        ).all()
        for receivable in receivables:
            amount = float(receivable.amount or 0)
            remaining = float(receivable.remaining_amount or 0)
            paid = amount - remaining
            
            total_receivables += amount
            total_received += paid
            total_pending += remaining
            if receivable.status == 'overdue':
                total_overdue += remaining
                
        print(f"Total a receber: R$ {total_receivables:.2f}")
        print(f"Total recebido: R$ {total_received:.2f}")
        print(f"Total pendente: R$ {total_pending:.2f}")
        print(f"Total vencido: R$ {total_overdue:.2f}")
            
        # Total a pagar
        total_payables = 0
        payables = Payable.query.filter(
            Payable.status.in_(['pending', 'partial', 'overdue'])
        ).all()
        print(f"Contas a pagar encontradas: {len(payables)}")
        for payable in payables:
            print(f"- ID: {payable.id}, Valor: {payable.amount}, Status: {payable.status}, Restante: {payable.remaining_amount}")
            total_payables += float(payable.remaining_amount or 0)
        print(f"Total a pagar: R$ {total_payables:.2f}")
        
        response_data = {
            'success': True,
            'data': {
                'sales': total_sales,
                'sales_last_7_days': total_last_7_days,
                'active_customers': active_customers,
                'low_stock': low_stock,
                'receivables': {
                    'total': total_receivables,
                    'received': total_received,
                    'pending': total_pending,
                    'overdue': total_overdue
                },
                'payables': total_payables
            }
        }
        print("\nRetornando dados:", response_data)
        return jsonify(response_data)
        
    except Exception as e:
        print('\n=== ERRO ao obter estatísticas ===')
        print(f"Tipo do erro: {type(e)}")
        print(f"Erro: {str(e)}")
        print("Traceback completo:")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/api/dashboard/recent')
@login_required
def get_recent_sales():
    """Retorna as vendas mais recentes"""
    try:
        sales = Sale.query.order_by(Sale.date.desc()).limit(5).all()
        return jsonify({
            'success': True,
            'data': [sale.to_dict() for sale in sales]
        })
        
    except Exception as e:
        import traceback
        print('Error in get_recent_sales:', str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/api/dashboard/top-selling')
@login_required
def get_top_selling():
    """Retorna os produtos mais vendidos"""
    try:
        today = date.today()
        
        # Calculate sales for each product using SQL aggregation
        top_products_query = db.session.query(
            Product,
            func.sum(SaleItem.price * SaleItem.quantity * (1 - SaleItem.discount/100)).label('total_amount'),
            func.sum(SaleItem.quantity).label('total_quantity')
        ).join(SaleItem).join(Sale).filter(
            func.date(Sale.date) == today
        ).group_by(Product.id).order_by(
            func.sum(SaleItem.price * SaleItem.quantity * (1 - SaleItem.discount/100)).desc()
        ).limit(5)

        # Format results
        top_products = []
        for product, total_amount, total_quantity in top_products_query.all():
            top_products.append({
                'product': product.to_dict(),
                'total_amount': float(total_amount or 0),
                'total_quantity': float(total_quantity or 0)
            })
        
        return jsonify({
            'success': True,
            'data': top_products
        })
        
    except Exception as e:
        import traceback
        print('Error in get_top_selling:', str(e))
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_bp.route('/gestao')
@login_required
def gestao():
    """Renderiza a página do dashboard"""
    try:
        today = date.today()
        
        # Vendas do dia
        total_sales = 0
        sales = Sale.query.filter(
            func.date(Sale.date) == today
        ).all()
        for sale in sales:
            total_sales += float(sale.total or 0)
            
        # Total a receber
        total_receivables = 0
        received = 0
        pending_receivables = 0
        total_overdue = 0
        receivables = Receivable.query.filter(
            Receivable.status.in_(['pending', 'partial', 'overdue'])
        ).all()
        for receivable in receivables:
            amount = float(receivable.amount or 0)
            remaining = float(receivable.remaining_amount or 0)
            paid = amount - remaining
            
            total_receivables += amount
            received += paid
            pending_receivables += remaining
            if receivable.status == 'overdue':
                total_overdue += remaining
                
        # Total a pagar
        total_payables = 0
        paid = 0
        pending_payables = 0
        payables = Payable.query.filter(
            Payable.status.in_(['pending', 'partial', 'overdue'])
        ).all()
        for payable in payables:
            amount = float(payable.amount or 0)
            remaining = float(payable.remaining_amount or 0)
            paid_amount = amount - remaining
            
            total_payables += amount
            paid += paid_amount
            pending_payables += remaining
            
        # Dados dos últimos 12 meses
        last_12_months = []
        sales_by_month = []
        for i in range(11, -1, -1):
            month_date = today - timedelta(days=i*30)
            last_12_months.append(month_date.strftime('%b/%Y'))
            
            month_sales = Sale.query.filter(
                func.extract('month', Sale.date) == month_date.month,
                func.extract('year', Sale.date) == month_date.year
            ).all()
            
            month_total = sum(float(sale.total or 0) for sale in month_sales)
            sales_by_month.append(month_total)
            
        # Dados para os cards do topo
        month_revenue = sales_by_month[-1]  # Último mês
        estimated_profit = month_revenue * 0.3  # 30% de lucro estimado
        
        # Crescimento em relação ao mês anterior
        if sales_by_month[-2] > 0:  # Se teve vendas no mês anterior
            growth = ((sales_by_month[-1] - sales_by_month[-2]) / sales_by_month[-2]) * 100
        else:
            growth = 100.0  # Se não teve vendas, crescimento de 100%
            
        # Média diária de vendas do mês atual
        days_in_month = today.day
        avg_daily_sales = month_revenue / days_in_month if days_in_month > 0 else 0
        
        # Top 5 produtos mais vendidos
        top_products_query = db.session.query(
            Product,
            func.sum(SaleItem.quantity).label('total_quantity')
        ).join(SaleItem).join(Sale).filter(
            func.date(Sale.date) == today
        ).group_by(Product.id).order_by(
            func.sum(SaleItem.quantity).desc()
        ).limit(5)

        top_products = []
        for product, total_quantity in top_products_query.all():
            top_products.append({
                'name': product.name,
                'total_quantity': float(total_quantity or 0)
            })
        
        return render_template(
            'management/dashboard.html',
            month_revenue=month_revenue,
            estimated_profit=estimated_profit,
            growth=growth,
            avg_daily_sales=avg_daily_sales,
            last_12_months=last_12_months,
            sales_by_month=sales_by_month,
            total_receivables=total_receivables,
            received=received,
            pending_receivables=pending_receivables,
            total_overdue=total_overdue,
            total_payables=total_payables,
            paid=paid,
            pending_payables=pending_payables,
            top_products=top_products
        )
        
    except Exception as e:
        print(f"Erro ao renderizar dashboard: {str(e)}")
        traceback.print_exc()
        return render_template('error.html', error=str(e))
