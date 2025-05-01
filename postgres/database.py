import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

user = os.getenv("POSTGRES_USER")
password = quote_plus(os.getenv("POSTGRES_PASSWORD"))
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")
db = os.getenv("POSTGRES_DB")

# SQLAlchemy 연결
engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")

# 한글 카테고리 → 영어 테이블명 매핑
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

# 업로드할 파일들
files = [
    "data/life.csv",
    "data/play.csv",
    "data/safety.csv",
    "data/traffic.csv",
    "data/health_care.csv"
]

for file_path in files:
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    if 'category' not in df.columns:
        continue

    for category, group_df in df.groupby('category'):
        table_name = category_mapping.get(category)

        if table_name:
            # 테이블 생성 쿼리
            with engine.connect() as conn:
                create_sql = f"""
                DROP TABLE IF EXISTS {table_name} CASCADE;
                CREATE TABLE {table_name} (
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
            print(f"⚠️ 카테고리 매핑 없음: {category}")

# users 테이블 생성
with engine.connect() as conn:
    create_users_sql = """
    DROP TABLE IF EXISTS users CASCADE;
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    GRANT ALL ON TABLE users TO teammate;
    GRANT USAGE, SELECT, UPDATE ON SEQUENCE users_id_seq TO teammate;
    """
    conn.execute(text(create_users_sql))
    print("users 테이블 생성 및 권한 부여 완료!")

# dagobang.csv 테이블 생성 및 삽입
csv_path = "data/dagobang.csv"
df_dagobang = pd.read_csv(csv_path, encoding="utf-8-sig")

with engine.connect() as conn:
    create_dagobang_sql = """
    DROP TABLE IF EXISTS officetels CASCADE;
    CREATE TABLE officetels (
        id SERIAL PRIMARY KEY,
        address TEXT,
        rent_type TEXT,
        deposit TEXT,
        monthly_fee TEXT,
        admin_fee TEXT,
        structure TEXT,
        exclusive_area TEXT,
        floor TEXT,
        building_use TEXT,
        direction TEXT,
        parking TEXT,
        elevator TEXT,
        available TEXT,
        built_year TEXT,
        agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn.execute(text(create_dagobang_sql))

# dagobang 데이터 삽입
if not df_dagobang.empty:
    df_dagobang.to_sql("officetels", engine, if_exists="append", index=False)
    print(f"officetels 테이블에 {len(df_dagobang)}개 행 삽입 완료!")
