import os
import pandas as pd
from math import radians, cos, sin, asin
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from sqlalchemy import create_engine

# 환경 설정
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")

if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(
            cloud=os.getenv("PINECONE_CLOUD"),
            region=os.getenv("PINECONE_REGION")
        )
    )
index = pc.Index(index_name)

db_url = os.getenv("DB_URL")
engine = create_engine(db_url)
station_df = pd.read_sql(
    "SELECT business_name AS station_name, latitude AS lat, longitude AS lng FROM traffic_subway",
    engine
)

# 거리 계산 함수
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(a**0.5)

# 가장 가까운 역 찾기
def find_nearest_station(user_lat, user_lng):
    station_df['dist'] = station_df.apply(lambda r: haversine(user_lat, user_lng, r.lat, r.lng), axis=1)
    nearest = station_df.loc[station_df.dist.idxmin()]
    return nearest.station_name, nearest.dist

# 임베딩 생성
def get_embedding(text):
    res = client.embeddings.create(model="text-embedding-ada-002", input=text)
    return res.data[0].embedding

def run_query_mode(user_lat, user_lng, rent, deposit, maint, station_name, time_limit, selected_infras):
    query_str = f"월세 {rent}만원, 보증금 {deposit}만원, 관리비 {maint}만원, 역: {station_name}, {time_limit}분 이내 이동"
    embedding = get_embedding(query_str)

    filter_cond = {
        'rent': {'$lte': rent},
        'deposit': {'$lte': deposit},
        'maint': {'$lte': maint}
    }

    res = index.query(vector=embedding, top_k=50, include_metadata=True, filter=filter_cond)

    def infra_score(md):
        return sum(md.get(key, 0) for key in selected_infras)

    matches = [
        m for m in res.matches
        if m.metadata.get("station") == station_name and m.metadata.get("walk_time", 999) <= time_limit
    ]

    matches = sorted(matches, key=lambda m: (infra_score(m.metadata), m.score), reverse=True)[:5]

    if not matches:
        print("조건에 맞는 매물이 없습니다.")
    for i, m in enumerate(matches, 1):
        md = m.metadata
        print(f"{i}. {md.get('address','주소 없음')} | 월세 {md.get('rent','?')}만 | 보증금 {md.get('deposit','?')}만 | 관리비 {md.get('maint','?')}만 | 평수 {md.get('size','?')}평 | 인프라 점수: {infra_score(md)} | 유사도: {m.score:.4f}")

if __name__ == "__main__":
    user_lat = 37.5055712636346
    user_lng = 126.941856308051
    station_name, _ = find_nearest_station(user_lat, user_lng)

    run_query_mode(
        user_lat=user_lat,
        user_lng=user_lng,
        rent=60,
        deposit=500,
        maint=10,
        station_name=station_name.split()[-1],
        time_limit=15,
        selected_infras=["infra_park", "infra_cafe"]
    )
