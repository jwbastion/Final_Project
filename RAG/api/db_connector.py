import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 설정
db_config = {
    'host': os.getenv("DB_HOST", "zipup-db.cnkoy8gkiz2v.ap-southeast-2.rds.amazonaws.com"),
    'database': os.getenv("DB_NAME", "postgres"),
    'user': os.getenv("DB_USER", "teammate"),
    'password': os.getenv("DB_PASSWORD", "teampass123"),
    'port': os.getenv("DB_PORT", "5432")
}

def get_connection():
    """데이터베이스 연결 객체 반환"""
    try:
        conn = psycopg2.connect(**db_config)
        return conn
    except Exception as e:
        print(f"데이터베이스 연결 오류: {e}")
        return None

def get_user_info(user_email=None, user_uuid=None):
    """사용자 정보 조회"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if user_email:
            cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
        elif user_uuid:
            cursor.execute("SELECT * FROM users WHERE user_uuid = %s", (user_uuid,))
        else:
            return None
        
        user_info = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return user_info
    except Exception as e:
        print(f"사용자 정보 조회 오류: {e}")
        if conn:
            conn.close()
        return None

def get_available_users():
    """사용 가능한 사용자 목록 조회"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT email, nickname, user_uuid, preferred_area, budget, monthly, maintenance_fee FROM users ORDER BY last_login_at DESC LIMIT 10")
        users = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return users
    except Exception as e:
        print(f"사용자 목록 조회 오류: {e}")
        if conn:
            conn.close()
        return []