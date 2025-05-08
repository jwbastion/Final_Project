from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS 
from dotenv import load_dotenv
import hashlib
import os
from datetime import datetime


# .env 로드
load_dotenv()

DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

# Flask 설정
app = Flask(__name__)
CORS(app)  
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

db = SQLAlchemy(app)

# 사용자 모델
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

# 비밀번호 해시 함수
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# 회원가입 API
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': '필수값 누락'}), 400

    if Users.query.filter_by(email=email).first():
        return jsonify({'error': '이미 존재하는 사용자'}), 409

    hashed_pw = hash_password(password)
    new_user = Users(email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': '회원가입 성공'}), 201

# 로그인 API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = hash_password(data.get('password'))

    user = Users.query.filter_by(email=email, password=password).first()

    if user:
        user.last_login_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': '로그인 성공', 'username': email}), 200
    else:
        return jsonify({'error': '로그인 실패'}), 401
    

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)
