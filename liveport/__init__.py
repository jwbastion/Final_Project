from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from liveport.config import Config

# 데이터베이스 인스턴스 생성
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, supports_credentials=True)
    db.init_app(app)

    # 블루프린트 등록
    from liveport.routes.user_route import user_bp
    from liveport.routes.chatbot_route import chatbot_bp

    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(chatbot_bp, url_prefix="/api")

    # 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
        
        # 라우트 목록 출력 (디버깅용)
        print("\n🔍 현재 등록된 라우트 목록:")
        for rule in app.url_map.iter_rules():
            print(f"{rule.endpoint:25s} | {', '.join(rule.methods):15s} | {rule}")

    return app