from flask import Blueprint, request, jsonify, g
from liveport.services.auth_service import token_required, generate_token
from liveport.services.user_service import create_user, verify_user
from liveport.models.user_model import db, Users

user_bp = Blueprint("user", __name__)

# 회원가입
@user_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    nickname = data.get("nickname")

    if not email or not password:
        return jsonify({"error": "필수값 누락"}), 400

    user = create_user(email, password, nickname)
    if user:
        return jsonify({"message": "회원가입 성공"}), 201
    else:
        return jsonify({"error": "이미 존재하는 사용자"}), 409

# 로그인 (JWT 토큰 발급)
@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    # 사용자 인증
    user = verify_user(email, password)
    if not user:
        return jsonify({"error": "로그인 실패: 이메일 또는 비밀번호가 잘못되었습니다."}), 401
    
    # 토큰 생성 (auth_service.py의 함수 사용)
    token = generate_token(user)
    if not token:
        return jsonify({"error": "토큰 생성 실패"}), 500
    
    # 응답 데이터
    return jsonify({
        "message": "로그인 성공",
        "token": token,
        "user": {
            "uuid": str(user.user_uuid),
            "email": user.email,
            "nickname": user.nickname or "사용자"
        }
    }), 200

# 설문 응답 저장 및 조회 통합 API
@user_bp.route("/survey", methods=["POST", "GET"])
@token_required
def survey():
    # GET 요청 처리 (설문 조회)
    if request.method == "GET":
        user = Users.query.filter_by(user_uuid=g.user_uuid).first()
        if not user:
            return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404

        return jsonify({
            "nickname": user.nickname,
            "preferred_area": user.preferred_area,
            "address": user.address,
            "latitude": user.latitude,
            "longitude": user.longitude,
            "budget": user.budget,
            "monthly": user.monthly,
            "maintenance_fee": user.maintenance_fee
        }), 200
    
    # POST 요청 처리 (설문 저장)
    elif request.method == "POST":
        data = request.get_json()
        
        user = Users.query.filter_by(user_uuid=g.user_uuid).first()
        if not user:
            return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404

        # 설문 데이터 저장
        if "preferred_area" in data:
            user.preferred_area = data.get("preferred_area")
        if "budget" in data:
            user.budget = data.get("budget")
        if "monthly" in data:
            user.monthly = data.get("monthly")
        if "maintenance_fee" in data:
            user.maintenance_fee = data.get("maintenance_fee")
        if "latitude" in data:
            user.latitude = data.get("latitude")
        if "longitude" in data:
            user.longitude = data.get("longitude")
        if "address" in data:
            user.address = data.get("address")

        db.session.commit()
        return jsonify({"message": "설문 결과 저장 완료"}), 200
    
# 사용자별 최신 설문 조회
@user_bp.route("/survey/latest", methods=["GET"])
def get_latest_survey():
    email = request.args.get("email")
    if not email:
        return jsonify({"error": "이메일이 필요합니다"}), 400
    
    user = Users.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "사용자를 찾을 수 없습니다"}), 404
    
    return jsonify({
        "nickname": user.nickname,
        "preferred_area": user.preferred_area,
        "address": user.address,
        "latitude": user.latitude,
        "longitude": user.longitude,
        "budget": user.budget,
        "monthly": user.monthly,
        "maintenance_fee": user.maintenance_fee
    }), 200