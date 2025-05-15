# debug_system.py
import psycopg2
from config import DB_CONFIG
import requests
import json
import uuid
import datetime
import jwt  # pip install PyJWT if not installed

def debug_system():
    """전체 시스템 워크플로우 디버깅"""
    # 0. 테이블 재생성 (선택적)
    recreate = input("테이블을 재생성하시겠습니까? (y/n): ")
    if recreate.lower() == 'y':
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_client_encoding('UTF8')
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS chat_history")
        cursor.execute("""
        CREATE TABLE chat_history (
            id SERIAL PRIMARY KEY,
            user_uuid VARCHAR(255) NOT NULL,
            message TEXT,
            response TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("테이블 재생성 완료")
    
    # 1. 직접 DB에 테스트 데이터 삽입
    conn = psycopg2.connect(**DB_CONFIG)
    conn.set_client_encoding('UTF8')
    cursor = conn.cursor()
    
    test_uuid = "0faf113d-a93c-4cf6-9754-75407369be9d"
    test_message = "DB 테스트: 한글 메시지"
    test_response = "DB 테스트: 한글 응답"
    
    cursor.execute(
        "INSERT INTO chat_history (user_uuid, message, response, created_at) VALUES (%s, %s, %s, NOW()) RETURNING id",
        (test_uuid, test_message, test_response)
    )
    
    inserted_id = cursor.fetchone()[0]
    conn.commit()
    
    # 삽입 확인
    cursor.execute("SELECT message, response FROM chat_history WHERE id = %s", (inserted_id,))
    saved_message, saved_response = cursor.fetchone()
    
    print(f"\n=== 직접 DB 삽입 테스트 (ID: {inserted_id}) ===")
    print(f"원본 메시지: {test_message}")
    print(f"저장된 메시지: {saved_message}")
    print(f"일치 여부: {'✓ 일치' if test_message == saved_message else '✗ 불일치'}")
    
    cursor.close()
    conn.close()
    
    # 2. API를 통해 테스트 데이터 삽입 - 수정된 버전
    
    # 방법 1: 직접 JWT 토큰 생성 (서버의 시크릿 키를 알고 있는 경우)
    try:
        # 사용자 UUID
        user_uuid = "0faf113d-a93c-4cf6-9754-75407369be9d"  # 33333@naver.com 사용자의 UUID
        
        # JWT 토큰 직접 생성 (서버의 시크릿 키가 필요)
        jwt_secret = "c784167e8eef4fcbe6f1a01fba80d648f2c8835c18d18f453d9484e785122faf"  # 서버에서 사용하는 JWT 시크릿 키
        
        token = jwt.encode(
            {
                "user_uuid": user_uuid, 
                "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
            }, 
            jwt_secret,             algorithm="HS256"
        )
        
        print(f"\n=== JWT 토큰 생성 성공 ===")
        print(f"토큰: {token[:20]}...")
        
        # 채팅 메시지 전송
        api_test_message = "API 테스트: 한글 메시지"
        
        chat_response = requests.post(
            "http://localhost:5000/api/chat/message",
            json={"message": api_test_message},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8"
            }
        )
        
        if chat_response.status_code == 200:
            print(f"\n=== API 메시지 전송 성공 ===")
            print(f"보낸 메시지: {api_test_message}")
            print(f"받은 응답: {chat_response.json().get('response')[:50]}...")
            
            # 채팅 이력 확인
            history_response = requests.get(
                "http://localhost:5000/api/chat/history?limit=1",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json; charset=utf-8"
                }
            )
            
            if history_response.status_code == 200:
                history = history_response.json().get("history", [])
                if history:
                    saved_api_message = history[0].get("message")
                    print(f"\n=== API 이력 확인 ===")
                    print(f"원본 메시지: {api_test_message}")
                    print(f"저장된 메시지: {saved_api_message}")
                    print(f"일치 여부: {'✓ 일치' if api_test_message == saved_api_message else '✗ 불일치'}")
                    
                    # 불일치인 경우 문자 비교
                    if api_test_message != saved_api_message:
                        print("\n문자 비교:")
                        for i, (orig, saved) in enumerate(zip(api_test_message, saved_api_message)):
                            if orig != saved:
                                print(f"위치 {i}: 원본 '{orig}' (0x{ord(orig):02x}) != 저장됨 '{saved}' (0x{ord(saved):02x})")
                        
                        # DB에서 직접 확인
                        conn = psycopg2.connect(**DB_CONFIG)
                        conn.set_client_encoding('UTF8')
                        cursor = conn.cursor()
                        
                        cursor.execute("SELECT id, message FROM chat_history ORDER BY id DESC LIMIT 1")
                        db_id, db_message = cursor.fetchone()
                        
                        print(f"\n=== DB 직접 확인 (ID: {db_id}) ===")
                        print(f"DB에서 가져온 메시지: {db_message}")
                        print(f"API 메시지와 일치 여부: {'✓ 일치' if api_test_message == db_message else '✗ 불일치'}")
                        print(f"이력 응답과 일치 여부: {'✓ 일치' if saved_api_message == db_message else '✗ 불일치'}")
                        
                        cursor.close()
                        conn.close()
                else:
                    print("이력이 없습니다.")
            else:
                print(f"이력 확인 실패: {history_response.status_code}")
        else:
            print(f"메시지 전송 실패: {chat_response.status_code}")
    except Exception as e:
        print(f"JWT 방식 API 테스트 오류: {e}")
        
    # 방법 2: UUID를 직접 전달하는 방식 (API가 이를 지원하는 경우)
    try:
        print("\n=== UUID 직접 전달 방식 테스트 ===")
        user_uuid = "0faf113d-a93c-4cf6-9754-75407369be9d"  # 33333@naver.com 사용자의 UUID
        api_test_message = "API 테스트: UUID 방식 메시지"
        
        # UUID를 요청 본문에 포함
        chat_response = requests.post(
            "http://localhost:5000/api/chat/message",
            json={"message": api_test_message, "user_uuid": user_uuid},
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
        if chat_response.status_code == 200:
            print(f"메시지 전송 성공: {chat_response.json().get('response')[:50]}...")
            
            # 이력 확인
            history_response = requests.get(
                f"http://localhost:5000/api/chat/history?limit=1&user_uuid={user_uuid}",
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
            if history_response.status_code == 200:
                print(f"이력 확인 성공: {history_response.json().get('history', [])[0].get('message') if history_response.json().get('history') else '이력 없음'}")
            else:
                print(f"이력 확인 실패: {history_response.status_code}")
        else:
            print(f"메시지 전송 실패: {chat_response.status_code}")
    except Exception as e:
        print(f"UUID 방식 API 테스트 오류: {e}")

if __name__ == "__main__":
    debug_system()