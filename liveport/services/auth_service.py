import jwt
from functools import wraps
from datetime import datetime, timedelta
from flask import current_app, request, jsonify, g
import hashlib

def hash_password(password):
    """비밀번호 해싱"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user):
    """사용자 정보로 JWT 토큰 생성"""
    try:
        # 토큰 만료 시간 설정
        expiration = datetime.utcnow() + timedelta(seconds=current_app.config['JWT_EXPIRATION'])
        exp_timestamp = int(expiration.timestamp())
        
        # 사용자 UUID를 문자열로 변환
        user_uuid_str = str(user.user_uuid if hasattr(user, 'user_uuid') else user['user_uuid'])
        
        # 통합된 토큰 페이로드
        payload = {
            'sub': user_uuid_str,  # JWT 표준 필드
            'user_uuid': user_uuid_str,  # 기존 RAG 시스템 호환성을 위해 유지
            'email': user.email if hasattr(user, 'email') else user['email'],
            'exp': exp_timestamp
        }
        
        # 토큰 생성
        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        return token
        
    except Exception as e:
        print(f"토큰 생성 오류: {type(e).__name__}: {e}")
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        print("🔍 요청 헤더:", request.headers)
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            print("🔍 Authorization 헤더:", auth_header)
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                print("🔍 추출된 토큰:", token)
        
        if not token:
            print("❌ 토큰 없음")
            return jsonify({'message': '토큰이 필요합니다!'}), 401
        
        try:
            print("🔍 토큰 디코딩 시도:", token[:20] + "...")
            print("🔍 JWT_SECRET:", current_app.config['JWT_SECRET'][:5] + "...")
            print("🔍 JWT_ALGORITHM:", current_app.config['JWT_ALGORITHM'])
            
            # 여기서 options 매개변수 추가 - 디버그용으로 만료 검증 비활성화
            payload = jwt.decode(
                token, 
                current_app.config['JWT_SECRET'], 
                algorithms=[current_app.config['JWT_ALGORITHM']],
                options={"verify_exp": False}  # 토큰 만료 검증 비활성화 (임시)
            )
            
            print("🔍 디코딩 성공! 페이로드:", payload)
            
            # 모든 페이로드 필드에 접근 가능하도록 g에 저장
            g.user_uuid = payload.get('user_uuid') or payload.get('sub')
            g.email = payload.get('email')
            
            print("🔍 g.user_uuid:", g.user_uuid)
            print("🔍 g.email:", g.email)
            
        except jwt.ExpiredSignatureError:
            print("❌ 토큰 만료")
            return jsonify({'message': '토큰이 만료되었습니다!'}), 401
        except jwt.InvalidTokenError as e:
            print(f"❌ 유효하지 않은 토큰: {str(e)}")
            return jsonify({'message': f'유효하지 않은 토큰입니다! 오류: {str(e)}'}), 401
        except Exception as e:
            print(f"❌ 기타 오류: {str(e)}")
            return jsonify({'message': f'토큰 처리 중 오류: {str(e)}'}), 401
        
        return f(*args, **kwargs)
    return decorated