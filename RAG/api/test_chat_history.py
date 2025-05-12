import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG

def check_pg_history(user_uuid):
    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT message, response, created_at
        FROM chat_history
        WHERE user_uuid = %s
        ORDER BY created_at DESC
    """, (user_uuid,))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("Postgres 에 해당 사용자의 대화 기록이 없습니다.")
    else:
        print(f"Postgres에 저장된 대화 기록 {len(rows)}개:")
        for r in rows[:3]:
            print(f"- 사용자: {r['message']}\n  챗봇: {r['response']}\n  저장시간: {r['created_at']}\n")
