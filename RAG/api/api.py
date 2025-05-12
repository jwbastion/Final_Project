from flask import Blueprint, request, jsonify, g
import jwt
import datetime
from functools import wraps
from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION, DB_CONFIG
from chatbot import RealEstateChatbot
import psycopg2
from psycopg2.extras import RealDictCursor

api_bp = Blueprint('api', __name__)

# JWT 인증 데코레이터
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # 헤더에서 토큰 추출
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': '토큰이 필요합니다!'}), 401
        
        try:
            # 토큰 디코딩
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            g.user_uuid = payload['user_uuid']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '토큰이 만료되었습니다!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '유효하지 않은 토큰입니다!'}), 401
        
        return f(*args, **kwargs)
    return decorated

# 로그인 API
@api_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': '이메일과 비밀번호를 입력하세요!'}), 400
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 테이블 존재 여부 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        table_exists = cursor.fetchone()
        
        if not table_exists or not table_exists[0]:
            # 테이블이 없으면 가상 데이터 사용
            print("users 테이블이 존재하지 않습니다. 가상 데이터를 사용합니다.")
            cursor.close()
            conn.close()
            
            # 시연용 계정 (이메일이 'test@example.com'이고 비밀번호가 'password'인 경우)
            if data.get('email') == 'test@example.com' and data.get('password') == 'password':
                # 가상 UUID 생성
                user_uuid = 'test-user-uuid-123'
                
                # JWT 토큰 생성
                token_payload = {
                    'user_uuid': user_uuid,
                    'email': data.get('email'),
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION)
                }
                
                token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
                
                return jsonify({
                    'token': token,
                    'user': {
                        'uuid': user_uuid,
                        'email': data.get('email'),
                        'nickname': '테스트 사용자'
                    }
                }), 200
            else:
                return jsonify({'message': '사용자를 찾을 수 없습니다!'}), 404
        
        # 테이블이 있으면 쿼리 실행
        query = """
        SELECT * FROM users 
        WHERE email = %s
        """
        
        cursor.execute(query, (data.get('email'),))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'message': '사용자를 찾을 수 없습니다!'}), 404
        
        # 비밀번호 검증 (실제 환경에서는 암호화된 비밀번호 비교)
        if data.get('password') != user['password']:
            return jsonify({'message': '비밀번호가 일치하지 않습니다!'}), 401
        
        # JWT 토큰 생성
        token_payload = {
            'user_uuid': user['user_uuid'],
            'email': user['email'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_EXPIRATION)
        }
        
        token = jwt.encode(token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # 마지막 로그인 시간 업데이트
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            update_query = """
            UPDATE users 
            SET last_login_at = NOW() 
            WHERE user_uuid = %s
            """
            
            cursor.execute(update_query, (user['user_uuid'],))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"로그인 시간 업데이트 오류: {e}")
        
        return jsonify({
            'token': token,
            'user': {
                'uuid': user['user_uuid'],
                'email': user['email'],
                'nickname': user['nickname']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'로그인 중 오류가 발생했습니다: {str(e)}'}), 500

# 채팅 메시지 처리 API
@api_bp.route('/chat/message', methods=['POST'])
@token_required
def chat_message():
    data = request.get_json()
    
    if not data or not data.get('message'):
        return jsonify({'message': '메시지를 입력하세요!'}), 400
    
    try:
        # 사용자 UUID로 챗봇 생성
        chatbot = RealEstateChatbot(g.user_uuid)
        
        # 메시지 처리
        response = chatbot.process_message(data.get('message'))
        
        return jsonify({
            'response': response
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'메시지 처리 중 오류가 발생했습니다: {str(e)}'}), 500

# 사용자 정보 조회 API
@api_bp.route('/user/profile', methods=['GET'])
@token_required
def get_user_profile():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 테이블 존재 여부 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'users'
            );
        """)
        table_exists = cursor.fetchone()
        
        if not table_exists or not table_exists[0]:
            # 테이블이 없으면 가상 데이터 사용
            print("users 테이블이 존재하지 않습니다. 가상 데이터를 사용합니다.")
            cursor.close()
            conn.close()
            
            # 가상 데이터 반환
            if g.user_uuid == 'test-user-uuid-123':
                return jsonify({
                    'user': {
                        'user_uuid': g.user_uuid,
                        'email': 'test@example.com',
                        'nickname': '테스트 사용자',
                        'created_at': datetime.datetime.now().isoformat(),
                        'last_login_at': datetime.datetime.now().isoformat(),
                        'budget': 50,
                        'monthly': 1000,
                        'maintenance_fee': 10,
                        'preferred_area': '강남',
                        'latitude': 37.498163,
                        'longitude': 127.027724,
                        'address': '서울시 강남구'
                    }
                }), 200
            else:
                return jsonify({'message': '사용자를 찾을 수 없습니다!'}), 404
        
        # 테이블이 있으면 쿼리 실행
        query = """
        SELECT user_uuid, email, nickname, created_at, last_login_at, 
               budget, monthly, maintenance_fee, preferred_area, 
               latitude, longitude, address
        FROM users 
        WHERE user_uuid = %s
        """
        
        cursor.execute(query, (g.user_uuid,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'message': '사용자를 찾을 수 없습니다!'}), 404
        
        return jsonify({
            'user': user
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'사용자 정보 조회 중 오류가 발생했습니다: {str(e)}'}), 500