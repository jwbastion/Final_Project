from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

from liveport import db

class Users(db.Model):
    __tablename__ = "users"
    # UUID 타입으로 변경하고 기본값 함수 추가
    user_uuid = db.Column(db.UUID, primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    nickname = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    
    # 설문 관련 필드
    budget = db.Column(db.Integer, nullable=True)
    monthly = db.Column(db.Integer, nullable=True)
    maintenance_fee = db.Column(db.Integer, nullable=True)
    preferred_area = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.String(100), nullable=True)

class UserState:
    def __init__(self, user_uuid=None):
        self.user_uuid = user_uuid
        self.state = {}
        self.history = []
        
        # DB에서 사용자 정보 로드
        if user_uuid:
            try:
                # 사용자 정보 조회 코드
                user = Users.query.filter_by(user_uuid=user_uuid).first()
                if user:
                    # 위치 정보 등 중요 정보 설정
                    self.state['lat'] = user.latitude
                    self.state['lng'] = user.longitude
                    # 기타 필요한 정보 설정
            except Exception as e:
                print(f"사용자 정보 로드 오류: {e}")
                
    def update(self, key, value):
        self.state[key] = value
        return self
        
    def get(self, key, default=None):
        return self.state.get(key, default)
        
    def add_to_history(self, user_message, bot_response):
        self.history.append({
            'user': user_message,
            'bot': bot_response
        })
        
    def get_history(self):
        return self.history