from flask import Blueprint, request, jsonify
from liveport.services.user_service import create_user, verify_user
from liveport.models.user_model import db, Users

user_bp = Blueprint('user', __name__)

# 회원가입
@user_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'error': '필수값 누락'}), 400

    user = create_user(email, password)
    if user:
        return jsonify({'message': '회원가입 성공'}), 201
    else:
        return jsonify({'error': '이미 존재하는 사용자'}), 409

# 로그인
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = verify_user(email, password)
    if user:
        return jsonify({'message': '로그인 성공', 'email': email}), 200
    else:
        return jsonify({'error': '로그인 실패'}), 401

# 설문 응답 저장
@user_bp.route('/survey', methods=['POST'])
def save_survey():
    data = request.get_json()
    print("[DEBUG] 받은 설문 데이터:", data)
    email = data.get('email')
    preferred_area = data.get('preferred_area')
    budget = data.get('budget')  # 보증금
    monthly = data.get('monthly')  # 월세
    maintenance_fee = data.get('maintenance_fee')
    address = data.get('address')          # 추가
    area_x = data.get('area_x')            # 위도
    area_y = data.get('area_y') 

    user = Users.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    user.preferred_area = preferred_area
    user.budget = budget
    user.monthly = monthly
    user.maintenance_fee = maintenance_fee
    user.address = address                 # 추가
    user.area_x = area_x                   # 추가
    user.area_y = area_y  

    db.session.commit()
    return jsonify({'message': '설문 결과 저장 완료'}), 200

# 설문 응답 조회 (최신)
@user_bp.route('/survey/latest', methods=['GET'])
def get_latest_survey():
    email = request.args.get('email')
    if not email:
        return jsonify({'error': '이메일 누락'}), 400

    user = Users.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'preferred_area': user.preferred_area,
        'budget': user.budget,
        'monthly': user.monthly,
        'maintenance_fee': user.maintenance_fee,
        'address': user.address,           # 추가
        'area_x': user.area_x,             # 추가
        'area_y': user.area_y 
    }), 200
