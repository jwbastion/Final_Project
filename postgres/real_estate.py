import json
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# DB 연결
conn = psycopg2.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD")
)
cur = conn.cursor()

# 테이블 생성
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
)
""")

# 데이터 삽입
with open("filtered_output.json", encoding="utf-8") as f:
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
        ON CONFLICT (id) DO NOTHING
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

conn.commit()
cur.close()
conn.close()
print("✅ 데이터베이스에 저장 완료")
