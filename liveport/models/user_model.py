from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
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
