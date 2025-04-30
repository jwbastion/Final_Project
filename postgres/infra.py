import os
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

# .env 파일 불러오기
load_dotenv()

# DB 연결 설정
user = os.getenv("POSTGRES_USER")
password = quote_plus(os.getenv("POSTGRES_PASSWORD"))
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")
db = os.getenv("POSTGRES_DB")

# 3. SQLAlchemy 엔진 생성
engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")

# 4. 한글 카테고리 → 영어 테이블명 매핑
category_mapping = {
    '대형마트': 'life_mart',
    '백화점': 'life_department_store',
    '공원': 'life_park',
    '우체국': 'life_post_office',
    '주민센터': 'life_community_center',
    '카페': 'life_cafe',
    '편의점': 'life_convenience_store',
    '다이소': 'life_daiso',
    '영화관': 'play_cinema',
    'PC방': 'play_pc_cafe',
    '노래방': 'play_karaoke',
    '파출소': 'safety_police_station',
    '버스': 'traffic_bus',
    '지하철': 'traffic_subway',
    '병원': 'health_hospital',
    '약국': 'health_pharmacy'
}

# 5. CSV 파일 목록
csv_files = [
    "data/main/life.csv",
    "data/main/play.csv",
    "data/main/safety.csv",
    "data/main/traffic.csv",
    "data/main/health_care.csv"
]

# 6. 카테고리별 테이블 생성 및 데이터 삽입
for file_path in csv_files:
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    if 'category' not in df.columns:
        continue

    for category, group_df in df.groupby('category'):
        table_name = category_mapping.get(category)

        if table_name:
            with engine.connect() as conn:
                create_sql = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    road_address TEXT,
                    business_name TEXT,
                    longitude REAL,
                    latitude REAL,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                conn.execute(text(create_sql))

            # 데이터 삽입
            group_df.to_sql(table_name, engine, if_exists="append", index=False)
            print(f"✅ {table_name} 테이블에 {len(group_df)}개 행 삽입 완료!")
        else:
            print(f"⚠️ 매핑되지 않은 카테고리: {category}")

with engine.connect() as conn:
    create_users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    -- 테이블 권한 부여
    GRANT ALL ON TABLE users TO teammate;
    -- 시퀀스 권한 부여
    GRANT USAGE, SELECT, UPDATE ON SEQUENCE users_id_seq TO teammate;
    """
    conn.execute(text(create_users_table_sql))
print(":흰색_확인_표시: users 테이블 생성 및 권한 부여 완료!")