from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)

from . import models, views # noqa

db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return models.User.query.get(user_id)

# https://www.youtube.com/shorts/wPt_yqT1PAw
# https://youtu.be/dl16e_mG6hg