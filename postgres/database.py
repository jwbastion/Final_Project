import os
import json
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# DB 연결 설정 (SQLAlchemy + psycopg2)
user = os.getenv("POSTGRES_USER")
password = quote_plus(os.getenv("POSTGRES_PASSWORD"))
host = os.getenv("POSTGRES_HOST")
port = os.getenv("POSTGRES_PORT")
db = os.getenv("POSTGRES_DB")

engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")
conn = psycopg2.connect(
    host=host,
    port=port,
    dbname=db,
    user=user,
    password=os.getenv("POSTGRES_PASSWORD")
)
cur = conn.cursor()

# listings 테이블 생성
cur.execute("""
CREATE TABLE IF NOT EXISTS listings (
    id TEXT PRIMARY KEY,
    address TEXT,
    house_type TEXT,
    floor TEXT,
    price_min REAL,
    price_max REAL,
    deposit_min REAL,
    deposit_max REAL,
    maintenance_fee REAL,
    gender TEXT,
    duration_min INTEGER,
    latitude REAL,
    longitude REAL,
    subway_station TEXT,
    subway_line TEXT,
    distance_to_station REAL
);
""")

# filtered_output.json → listings 테이블로 삽입
with open("data/filtered_output.json", encoding="utf-8") as f:
    data = json.load(f)

for _, row in data.items():
    cur.execute("""
        INSERT INTO listings (
            id, address, house_type, floor,
            price_min, price_max, deposit_min, deposit_max,
            maintenance_fee, gender, duration_min,
            latitude, longitude, subway_station, subway_line, distance_to_station
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
    """, (
        row.get("ID"),
        row.get("ADDR_FULL_ROAD"),
        row.get("HOUSE_TYPE_NM"),
        row.get("FLOOR"),
        float(row.get("PRICE_MIN") or 0),
        float(row.get("PRICE_MAX") or 0),
        float(row.get("DEPOSIT_MIN") or 0),
        float(row.get("DEPOSIT_MAX") or 0),
        float(row.get("MAINTENANCE_FEE") or 0),
        row.get("GENDER_TYPE_NM"),
        int(row.get("DURATION_MIN") or 0),
        float(row.get("LATITUDE") or 0),
        float(row.get("LONGITUDE") or 0),
        row.get("지하철역"),
        row.get("호선"),
        float(row.get("역까지거리(km)") or 0)
    ))

print(" listings 데이터 삽입 완료")

# infra 관련 CSV 데이터 삽입 처리
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

csv_files = [
    "data/life.csv",
    "data/play.csv",
    "data/safety.csv",
    "data/traffic.csv",
    "data/health_care.csv"
]

for file_path in csv_files:
    df = pd.read_csv(file_path, encoding="utf-8-sig")

    if 'category' not in df.columns:
        continue

    for category, group_df in df.groupby('category'):
        table_name = category_mapping.get(category)

        if table_name:
            with engine.connect() as conn_sql:
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
                conn_sql.execute(text(create_sql))

            group_df.to_sql(table_name, engine, if_exists="append", index=False)
            print(f"{table_name} 테이블에 {len(group_df)}개 행 삽입 완료!")
        else:
            print(f"매핑되지 않은 카테고리: {category}")

# users 테이블 생성 및 권한 부여
with engine.connect() as conn_sql:
    create_users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    GRANT ALL ON TABLE users TO teammate;
    GRANT USAGE, SELECT, UPDATE ON SEQUENCE users_id_seq TO teammate;
    """
    conn_sql.execute(text(create_users_table_sql))

print("users 테이블 생성 및 권한 부여 완료")

conn.commit()
cur.close()
conn.close()