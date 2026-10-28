from flask import Flask
from flask_wtf import CSRFProtect
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
csrf = CSRFProtect(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login' #caso seja necessario login.html futuramente

from app import routes, models

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return models.Usuario.query.get(int(user_id))