import win32print
import win32con
from models import CompanyInfo, Sale
from datetime import datetime
import traceback
import os
import sys
import logging
from fpdf import FPDF

# Configura logging
log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'printer.log')
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

# Tenta criar o diretório de cupons
try:
    receipts_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'receipts')
    if not os.path.exists(receipts_dir):
        os.makedirs(receipts_dir)
    logging.info(f"Diretório de cupons criado/verificado: {receipts_dir}")
except Exception as e:
    logging.error(f"Erro ao criar diretório de cupons: {str(e)}")

class ReceiptPDF(FPDF):
    def __init__(self):
        # 80mm = 8cm = aproximadamente 3.14961 polegadas
        # Reduzindo a largura para 70mm para garantir que caiba
        super().__init__(format=(70, 200))  # 70mm de largura
        self.set_margins(0.5, 0.5, 0.5)  # Margens mínimas: 0.5mm
        self.set_auto_page_break(auto=True, margin=0.5)
        self.add_page()
        self.set_font('Courier', '', 7)  # Fonte ainda menor: 7pt
        self.cell_height = 2.5  # Altura menor: 2.5mm
        self.line_width = 32  # Reduzido para caber na largura menor
        
    def add_line(self, text, font_name='Courier', style='', size=7):
        """Adiciona uma linha de texto com a fonte especificada"""
        self.set_font(font_name, style, size)
        # Quebra o texto em múltiplas linhas se necessário
        words = text.split()
        line = ''
        for word in words:
            test_line = f"{line} {word}".strip()
            if len(test_line) <= self.line_width:
                line = test_line
            else:
                self.cell(0, self.cell_height, line, ln=True)
                line = word
        if line:
            self.cell(0, self.cell_height, line, ln=True)
        
    def add_centered_line(self, text, font_name='Courier', style='', size=7):
        """Adiciona uma linha de texto centralizada"""
        self.set_font(font_name, style, size)
        # Quebra o texto em múltiplas linhas se necessário
        while len(text) > self.line_width:
            part = text[:self.line_width]
            text = text[self.line_width:]
            self.cell(0, self.cell_height, part.center(self.line_width), ln=True)
        if text:
            self.cell(0, self.cell_height, text.center(self.line_width), ln=True)
        
    def add_separator(self, char='-'):
        """Adiciona uma linha separadora"""
        self.cell(0, self.cell_height, char * self.line_width, ln=True)
        
    def add_double_line(self, left_text, right_text, font_name='Courier', style='', size=7):
        """Adiciona uma linha com texto à esquerda e à direita"""
        self.set_font(font_name, style, size)
        # Garante que o texto caiba
        max_left_width = self.line_width - len(right_text) - 1
        if len(left_text) > max_left_width:
            # Se o texto da esquerda for muito longo, quebra em duas linhas
            self.add_line(left_text)
            self.cell(0, self.cell_height, right_text.rjust(self.line_width), ln=True)
        else:
            # Se couber tudo em uma linha
            left_text = left_text[:max_left_width]
            text = f"{left_text}{' ' * (max_left_width - len(left_text))}{right_text}"
            self.cell(0, self.cell_height, text, ln=True)

def print_test(printer_name=None):
    """Imprime um cupom de teste"""
    try:
        logging.info("=== Iniciando impressão de teste ===")
        company = CompanyInfo.query.first()
        
        # Cria o PDF
        pdf = ReceiptPDF()
        
        # Cabeçalho
        pdf.add_centered_line(company.name, size=7)
        if company.address:
            pdf.add_centered_line(company.address, size=6)
        pdf.add_separator()
        pdf.add_centered_line("CUPOM DE VENDA", style='B', size=7)
        pdf.add_separator()
        
        # Dados da venda
        pdf.add_double_line("Venda #", "8")
        pdf.add_double_line("Data", datetime.now().strftime("%d/%m/%Y %H:%M"))
        pdf.add_double_line("Total", f"R$ {45.36:.2f}")
        pdf.add_separator()
        
        # Itens
        pdf.add_centered_line("ITENS")
        pdf.add_separator('-')
        pdf.add_line("Papel Higiênico")
        pdf.add_double_line("3.000 x R$ 15.12", f"R$ {45.36:.2f}")
        pdf.add_separator('-')
        
        # Total
        pdf.add_double_line("TOTAL", f"R$ {45.36:.2f}")
        pdf.add_separator()
        
        # Rodapé
        pdf.add_centered_line(f"{company.name}", size=6)
        pdf.add_centered_line("JC Byte Soluções em Tecnologia | Versão: 1.0.0.1", size=5)
        
        # Salva o PDF
        pdf_file = os.path.join(receipts_dir, 'cupom_teste.pdf')
        pdf.output(pdf_file)
        logging.info("PDF gerado com sucesso")
        return True
            
    except Exception as e:
        logging.error(f"Erro ao gerar PDF: {str(e)}")
        logging.error(traceback.format_exc())
        return False

def print_receipt(sale, printer_name=None):
    """Imprime o cupom de venda"""
    try:
        logging.info("=== Iniciando impressão do cupom ===")
        logging.info(f"Sale ID: {getattr(sale, 'id', 'N/A')}")
        
        # Verifica se o objeto sale é válido
        if not sale:
            logging.error("Objeto sale é None")
            return False
            
        if not isinstance(sale, Sale):
            logging.error(f"Objeto sale não é do tipo Sale. Tipo atual: {type(sale)}")
            return False
            
        # Verifica se tem os atributos necessários
        required_attrs = ['id', 'date', 'total', 'items']
        for attr in required_attrs:
            if not hasattr(sale, attr):
                logging.error(f"Objeto sale não tem o atributo {attr}")
                return False
                
        logging.info(f"Objeto sale validado. ID: {sale.id}, Total: {sale.total}")
        
        # Busca informações da empresa
        company = CompanyInfo.query.first()
        if not company:
            logging.error("Configurações da empresa não encontradas")
            return False
            
        # Tenta salvar na raiz do projeto
        try:
            pdf_file = os.path.join(receipts_dir, f'cupom_{sale.id}.pdf')
            logging.info(f"Caminho do arquivo: {pdf_file}")
        except Exception as e:
            logging.error(f"Erro ao definir caminho do arquivo: {str(e)}")
            return False
            
        # Prepara o PDF
        try:
            pdf = ReceiptPDF()
            
            # Adiciona cabeçalho da empresa
            if company.print_header:
                header = company.print_header.format(
                    empresa=company.name or '',
                    endereco=company.address or '',
                    cidade=company.city or '',
                    estado=company.state or '',
                    cnpj=company.cnpj or '',
                    ie=company.ie or ''
                )
                for line in header.split('\n'):
                    pdf.add_centered_line(line, size=7)
            
            # Adiciona informações da venda
            pdf.add_separator('=')
            pdf.add_centered_line("CUPOM DE VENDA", style='B', size=7)
            pdf.add_separator('=')
            
            pdf.add_double_line("Venda #", str(sale.id))
            pdf.add_double_line("Data", sale.date.strftime('%d/%m/%Y %H:%M:%S'))
            pdf.add_double_line("Operador", sale.supervisor.name)
            pdf.add_double_line("Total", f"R$ {float(sale.total):.2f}")
            pdf.add_separator('=')
            
            pdf.add_centered_line("ITENS")
            pdf.add_separator('-')
            
            # Adiciona os itens
            for item in sale.items:
                # Nome do produto
                product_name = item.product.name
                if len(product_name) > pdf.line_width - 3:
                    product_name = product_name[:pdf.line_width - 3] + "..."
                pdf.add_line(product_name)
                
                # Quantidade e preço unitário
                pdf.add_double_line(
                    f"{float(item.quantity):.3f} x R$ {float(item.price):.2f}",
                    f"R$ {float(item.quantity * item.price):.2f}"
                )
                pdf.add_line("")  # Espaço entre itens
                
            pdf.add_separator('-')
            pdf.add_double_line("TOTAL", f"R$ {float(sale.total):.2f}")
            
            # Adiciona informações de pagamento
            pdf.add_separator('=')
            pdf.add_centered_line("PAGAMENTO", style='B', size=7)
            pdf.add_separator('-')
            
            # Obtém o primeiro pagamento (normalmente só tem um)
            payment = sale.payments[0] if sale.payments else None
            if payment:
                pdf.add_double_line("Forma", payment.method.upper())
                if payment.method.lower() == 'dinheiro':
                    pdf.add_double_line("Valor Recebido", f"R$ {float(payment.received_amount):.2f}")
                    troco = float(payment.received_amount) - float(sale.total)
                    pdf.add_double_line("Troco", f"R$ {troco:.2f}")
            else:
                pdf.add_double_line("Forma", sale.payment_method.upper() if sale.payment_method else "N/A")
            
            pdf.add_separator('=')
            
            # Se tiver cliente vinculado, adiciona as informações
            if sale.customer:
                pdf.add_line("")  # Espaço antes
                pdf.add_centered_line("CLIENTE", style='B', size=7)
                pdf.add_separator('-')
                pdf.add_line(f"Nome: {sale.customer.name}")
                if sale.customer.registration:
                    pdf.add_line(f"Matrícula: {sale.customer.registration}")
                pdf.add_line("")  # Espaço antes da assinatura
                pdf.add_separator('-')
                pdf.add_line("")  # Espaço para assinatura
                pdf.add_line("")  # Espaço para assinatura
                pdf.add_centered_line("Assinatura do Cliente")
                pdf.add_line("")  # Espaço após
            
            # Adiciona rodapé da empresa em uma linha
            if company.print_footer:
                # Junta todas as linhas em uma só
                footer = ' | '.join(line.strip() for line in company.print_footer.split('\n') if line.strip())
                pdf.add_centered_line(footer, size=6)  # Fonte pequena mas legível
            
            # Adiciona copyright no rodapé
            pdf.add_centered_line("JC Byte Soluções em Tecnologia | Versão: 1.0.0.1", size=5)
            
            # Salva o PDF
            pdf.output(pdf_file)
            logging.info("PDF gerado com sucesso")
            return True
            
        except Exception as e:
            logging.error(f"Erro ao gerar PDF: {str(e)}")
            logging.error(traceback.format_exc())
            return False
            
    except Exception as e:
        logging.error(f"Erro geral: {str(e)}")
        logging.error(traceback.format_exc())
        return False
