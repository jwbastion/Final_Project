from functools import wraps
from flask import request, jsonify, g, current_app
import jwt

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
            # 토큰 검증
            payload = jwt.decode(
                token, 
                current_app.config.get('JWT_SECRET_KEY'), 
                algorithms=[current_app.config.get('JWT_ALGORITHM', 'HS256')]
            )
            
            # 사용자 정보를 g 객체에 저장
            g.user_uuid = payload['user_uuid']
            g.email = payload['email']
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '토큰이 만료되었습니다!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '유효하지 않은 토큰입니다!'}), 401
        
        return f(*args, **kwargs)
    
    return decorated