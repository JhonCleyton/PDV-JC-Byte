from flask import Flask, request
from models import db, Customer
from routes.customers import customers_bp
from flask_login import LoginManager, login_required, current_user, login_user
import functools

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdv.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'test_key'
db.init_app(app)

# Configurar login manager
login_manager = LoginManager()
login_manager.init_app(app)

# Mock current_user
class MockUser:
    @property
    def is_authenticated(self):
        return True
        
    @property
    def is_active(self):
        return True
        
    @property
    def is_anonymous(self):
        return False
        
    def get_id(self):
        return "1"

@login_manager.user_loader
def load_user(user_id):
    return MockUser()

# Registrar o blueprint
app.register_blueprint(customers_bp)

def test_route():
    with app.test_client() as client:
        # Fazer login
        with client.session_transaction() as session:
            session['_user_id'] = "1"
            session['_fresh'] = True
        
        print("\n=== Testando rota /api/clientes/1103 ===")
        response = client.get('/api/clientes/1103')
        print(f"Status: {response.status_code}")
        print(f"Data: {response.get_json()}")
        
        print("\n=== Testando rota /api/clientes/0001 ===")
        response = client.get('/api/clientes/0001')
        print(f"Status: {response.status_code}")
        print(f"Data: {response.get_json()}")
        
        print("\n=== Testando rota /api/clientes/06911499500 ===")
        response = client.get('/api/clientes/06911499500')
        print(f"Status: {response.status_code}")
        print(f"Data: {response.get_json()}")

if __name__ == '__main__':
    test_route()
