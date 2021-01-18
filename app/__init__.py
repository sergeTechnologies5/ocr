from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_bootstrap import Bootstrap
from flask_login import LoginManager

app = Flask(__name__)

CORS(app)
Bootstrap(app)
login = LoginManager(app)

login.login_view = 'login'
app.config.from_object(Config)
db = SQLAlchemy(app)

async_mode = None
socketio = SocketIO(app, async_mode=async_mode)

migrate = Migrate(app, db)
from app import routes, models, errors