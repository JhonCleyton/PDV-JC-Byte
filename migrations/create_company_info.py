from app import app, db
from models import CompanyInfo

def create_company_info_table():
    """Cria a tabela de informações da empresa"""
    with app.app_context():
        # Cria a tabela
        db.create_all()
        
        # Verifica se já existe um registro
        company = CompanyInfo.query.first()
        if not company:
            # Cria um registro inicial
            company = CompanyInfo(
                name='',
                cnpj='',
                ie='',
                address='',
                city='',
                state='',
                zip_code='',
                phone='',
                email='',
                printer_name='',
                print_header='',
                print_footer='',
                auto_print=True
            )
            db.session.add(company)
            db.session.commit()
            print('Registro inicial de company_info criado')
        else:
            print('Tabela company_info já existe')

if __name__ == '__main__':
    create_company_info_table()
