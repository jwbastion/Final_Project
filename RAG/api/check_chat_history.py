import os
import json
import time
import sqlite3

def check_chat_history(user_uuid):
    """사용자의 채팅 이력 저장 여부 확인"""
    # 1. 파일 저장 확인
    file_path = f"user_data/{user_uuid}.json"
    file_history_exists = False
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                chat_history = data.get('chat_history', [])
                
                if chat_history:
                    print(f"파일에 저장된 대화 기록 {len(chat_history)}개 발견")
                    for i, entry in enumerate(chat_history[:3], 1):  # 처음 3개만 출력
                        print(f"{i}. 사용자: {entry.get('user')}")
                        print(f"   챗봇: {entry.get('bot')}")
                        print(f"   타임스탬프: {time.ctime(entry.get('timestamp'))}")
                    
                    if len(chat_history) > 3:
                        print(f"... 외 {len(chat_history)-3}개 대화")
                    
                    file_history_exists = True
                else:
                    print("파일에 저장된 대화 기록이 없습니다.")
        except Exception as e:
            print(f"파일 읽기 오류: {e}")
    else:
        print(f"대화 기록 파일({file_path})이 존재하지 않습니다.")
    
    # 2. DB 저장 확인 - 실제 테이블 구조에 맞게 수정
    db_history_exists = False
    try:
        conn = sqlite3.connect('chatbot.db')
        cursor = conn.cursor()
        
        # 테이블 존재 여부 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_history'")
        if cursor.fetchone():
            # 실제 테이블 구조: id | user_uuid | message | response | created_at
            cursor.execute("SELECT message, response, created_at FROM chat_history WHERE user_uuid=? ORDER BY created_at DESC LIMIT 3", (user_uuid,))
            rows = cursor.fetchall()
            
            if rows:
                print(f"\nDB에 저장된 대화 기록 발견")
                cursor.execute("SELECT COUNT(*) FROM chat_history WHERE user_uuid=?", (user_uuid,))
                total_count = cursor.fetchone()[0]
                print(f"총 {total_count}개의 대화 기록이 DB에 저장됨")
                
                for i, row in enumerate(rows, 1):
                    print(f"{i}. 사용자: {row[0]}")
                    print(f"   챗봇: {row[1]}")
                    print(f"   타임스탬프: {row[2]}")
                
                if total_count > 3:
                    print(f"... 외 {total_count-3}개 대화")
                
                db_history_exists = True
            else:
                print("\nDB에 해당 사용자의 대화 기록이 없습니다.")
        else:
            print("\nDB에 chat_history 테이블이 존재하지 않습니다.")
            
            # 다른 테이블 이름 확인
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            if tables:
                print("존재하는 테이블 목록:")
                for table in tables:
                    print(f"- {table[0]}")
                    
                    # 각 테이블의 구조 확인
                    cursor.execute(f"PRAGMA table_info({table[0]})")
                    columns = cursor.fetchall()
                    print(f"  컬럼: {', '.join(col[1] for col in columns)}")
                    
                    # 사용자 UUID로 검색 시도
                    if 'user_uuid' in [col[1] for col in columns]:
                        cursor.execute(f"SELECT COUNT(*) FROM {table[0]} WHERE user_uuid=?", (user_uuid,))
                        count = cursor.fetchone()[0]
                        print(f"  이 테이블에 사용자의 데이터 {count}개 있음")
            else:
                print("데이터베이스에 테이블이 없습니다.")
    except Exception as e:
        print(f"\nDB 연결 오류: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    return file_history_exists, db_history_exists

# 사용 예시
user_uuid = "0faf113d-a93c-4cf6-9754-75407369be9d"  # 확인하려는 사용자 UUID
file_exists, db_exists = check_chat_history(user_uuid)

if file_exists or db_exists:
    print("\n✅ 채팅 이력이 저장되어 있습니다.")
else:
    print("\n❌ 채팅 이력이 저장되어 있지 않습니다.")
