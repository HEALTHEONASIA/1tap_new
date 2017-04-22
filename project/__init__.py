from flask import Flask
from flask import session, g
from flask_cors import CORS, cross_origin
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager
from flask_login import current_user
from .config import config
from flask_mail import Mail
from datetime import timedelta

db = SQLAlchemy()
mail = Mail()
login_manager = LoginManager()
socket_io = SocketIO()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'

def create_app(config_name):
    app = Flask(__name__)
    cors = CORS(app, resources={r"/api/*": {"origins": 
        "*"}})
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    # Auto Time Out After 60 Minutes For Session
    @app.before_request
    def before_request():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(minutes=60)
        session.modified = True
        g.user = current_user

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    socket_io.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    from . import views, models
    return app