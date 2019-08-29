
from flask_security.utils import encrypt_password
from datetime import datetime

def create_initial_admin_user(app):
    with app.app_context():
        user = app.db.users.insert(**dict(
            id=1, email='admin@example.com',
            password=encrypt_password('password'),
            active=True, confirmed_at=datetime.utcnow()))
        role = app.db.roles.insert(**dict(
            id=1, name='superuser', description='Someone who can do anything'
        ))
        app.db.commit()
        app.db.users_roles.insert(**dict(
            id=1, role_id=1, user_id=1
        ))
        app.db.commit()
