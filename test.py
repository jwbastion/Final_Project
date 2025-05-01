import psycopg2
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

# 환경변수에서 DB 설정 읽기
db_config = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD")
}

# DB 연결
conn = psycopg2.connect(**db_config)
cur = conn.cursor()

# 테이블 생성
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
)
""")

# 테스트 데이터 삽입
cur.execute("""
INSERT INTO users (email, password)
VALUES (%s, %s)
""", ('test@example.com', 'hashedpassword123'))

# 커밋 및 종료
conn.commit()
cur.close()
conn.close()

print("✅ users 테이블 생성 및 데이터 삽입 완료")
