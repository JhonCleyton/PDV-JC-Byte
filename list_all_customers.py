from models import db, Customer
from app import app

with app.app_context():
    print("\nClientes cadastrados:")
    for c in Customer.query.all():
        print(f"- {c.name} (ID: {c.id}, Matrícula: {c.registration})")
