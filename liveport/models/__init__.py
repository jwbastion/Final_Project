from flask import Flask
from flask_cors import CORS
from liveport.models.user_model import db, Users
from liveport.routes.user_route import user_bp
from liveport.config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    db.init_app(app)

    app.register_blueprint(user_bp)

    with app.app_context():
        db.create_all()

    return app
