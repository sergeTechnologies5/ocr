from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

async_mode = None
socketio = SocketIO(app, async_mode=async_mode)

migrate = Migrate(app, db)
from app import routes, models, errors