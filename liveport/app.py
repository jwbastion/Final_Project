from flask import Flask
from liveport.models.user_model import db
from dotenv import load_dotenv
import os

# 블루프린트 가져오기
from liveport.routes.user_route import user_bp  
from liveport.routes.chatbot_route import chatbot_bp  
from liveport.routes.recommendation_route import recommendation_bp

def create_app():
    app = Flask(__name__)
    
    # 설정 로드
    from liveport.config import Config 
    app.config.from_object(Config)
    
    # 데이터베이스 초기화
    db.init_app(app)
    
    # CORS 설정
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    # 블루프린트 등록
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(chatbot_bp, url_prefix='/api/chatbot')
    app.register_blueprint(recommendation_bp)
    
    @app.route('/')
    def index():
        return "통합 API 서버가 실행 중입니다."
    
    # 데이터베이스 테이블 생성
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)