from flask import Flask, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import os
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import base64

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default_secret_key')
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    db.init_app(app)

    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except Exception as e:
        print(f"Error creating instance path: {e}")

    from . import routes
    app.register_blueprint(routes.bp)

    from .owner_panel import owner_bp
    app.register_blueprint(owner_bp)

    from .admin_panel import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin_panel')

    from .models import Login, Customer, TurfOwner, Turf
    admin = Admin(app, name='Turf Booking Admin', template_mode='bootstrap3', url='/admin')

    class SecureModelView(ModelView):
        def is_accessible(self):
            return session.get('login_type') == 'admin'

        def inaccessible_callback(self, name, **kwargs):
            return redirect(url_for('main.login'))

    admin.add_view(SecureModelView(Login, db.session))
    admin.add_view(SecureModelView(Customer, db.session))
    admin.add_view(SecureModelView(TurfOwner, db.session))
    admin.add_view(SecureModelView(Turf, db.session))

    # Custom filter for base64 encoding
    def b64encode(data):
        return base64.b64encode(data).decode('utf-8')

    # Register the custom filter with Jinja2
    app.jinja_env.filters['b64encode'] = b64encode

    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Error initializing the database: {e}")

    return app