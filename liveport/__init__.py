from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from liveport.config import Config
from liveport.models.user_model import db
from liveport.routes.user_route import user_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)
    db.init_app(app)
    app.register_blueprint(user_bp, url_prefix="/api")

    with app.app_context():
        print("\n🔍 현재 등록된 라우트 목록:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint:25s} | {', '.join(rule.methods):15s} | {rule}")

    return app
