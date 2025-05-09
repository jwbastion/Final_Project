import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.db_config import DB_URI

# SQLAlchemy 엔진 및 세션 설정
engine = create_engine(DB_URI)
Session = sessionmaker(bind=engine)

# 로드할 테이블 목록
TABLES = [
    'health_hospital', 'health_pharmacy',
    'life_cafe', 'life_community_center', 'life_convenience_store',
    'life_daiso', 'life_department_store', 'life_mart', 'life_park', 'life_post_office',
    'officetels',
    'play_cinema', 'play_karaoke', 'play_pc_cafe',
    'safety_police_station',
    'traffic_bus', 'traffic_subway'
]

def normalize_coords(df):
    if 'lat' in df.columns and 'lng' in df.columns:
        return df.rename(columns={'lat':'latitude','lng':'longitude'})
    if 'latitude' in df.columns and 'longitude' in df.columns:
        return df
    if '위도' in df.columns and '경도' in df.columns:
        return df.rename(columns={'위도':'latitude','경도':'longitude'})
    raise ValueError(f"위경도 칼럼을 찾을 수 없습니다: {df.columns.tolist()}")

def load_infra_from_db():
    infra = {}
    for tbl in TABLES:
        df = pd.read_sql_table(tbl, con=engine)
        try:
            df = normalize_coords(df)
        except ValueError as e:
            print(f"⚠️  {tbl} 스킵: {e}")
            continue
        infra[tbl] = df
    return infra

# 테스트 코드
if __name__ == '__main__':
    dfs = load_infra_from_db()
    for name, df in dfs.items():
        print(f"Loaded {name}: {len(df)} rows")
