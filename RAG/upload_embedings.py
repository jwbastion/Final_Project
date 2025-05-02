import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
import re

# 1. 환경변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")
cloud = os.getenv("PINECONE_CLOUD")
region = os.getenv("PINECONE_REGION")

# 2. Pinecone 인덱스 생성 (없을 경우만)
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud=cloud, region=region)
    )
index = pc.Index(index_name)

# 3. 매물.csv 로드
df = pd.read_csv("Data/Data.csv", encoding="utf-8")

# 4. 전처리
df["층수"] = df["층수"].fillna("미확인").astype(str)
df["주실 방향"] = df["주실 방향"].fillna("미정")

# 5. 임베딩 텍스트 생성
df["embed_text"] = (
    df["지번주소"]
    + ", 월세 " + df["월세(만원)"].astype(str) + "만"
    + ", 보증금 " + df["보증금(만원)"].astype(str) + "만"
    + ", 관리비 " + df["관리비(만원)"].astype(str) + "만"
    + ", 평수 " + df["평수"].astype(str) + "평"
    + ", 방향 " + df["주실 방향"]
    + ", " + df["층수"] + "층"
    + ", 소요시간 " + df["소요시간"]
)

# 6. 소요시간 파싱 함수
def extract_time_by_type(text, keyword):
    text = str(text)
    match = re.search(rf"{keyword} 약 (\d+)분", text)
    return int(match.group(1)) if match else 9999

def extract_station_name(text):
    text = str(text)
    match = re.match(r"([가-힣0-9]+역)", text)
    return match.group(1) if match else "미확인역"

# 7. 시간 및 역 이름 파싱 추가
df["walk_time"] = df["소요시간"].apply(lambda x: extract_time_by_type(x, "도보"))
df["transit_time"] = df["소요시간"].apply(lambda x: extract_time_by_type(x, "대중교통"))
df["station"] = df["소요시간"].apply(extract_station_name)

# 8. OpenAI 임베딩 + Pinecone 업서트
batch_size = 50
records = []

for i, row in df.iterrows():
    try:
        res = client.embeddings.create(
            model="text-embedding-ada-002",
            input=row["embed_text"]
        )
        embedding = res.data[0].embedding

        meta = {
            "id": str(i),
            "address": row["지번주소"],
            "rent": float(row["월세(만원)"]),
            "deposit": float(row["보증금(만원)"]),
            "maint": float(row["관리비(만원)"]),
            "size": float(row["평수"]),
            "direction": row["주실 방향"],
            "floor": row["층수"],
            "walk_time": int(row["walk_time"]),
            "transit_time": int(row["transit_time"]),
            "station": row["station"],
            "subway_time": row["소요시간"],
            "lat": float(row["lat"]),
            "lng": float(row["lng"])
        }

        records.append((str(i), embedding, meta))

        if len(records) >= batch_size:
            index.upsert(vectors=records)
            print(f"✅ {i}번까지 업서트 완료")
            records = []

    except Exception as e:
        print(f"❌ row {i} 실패: {e}")

if records:
    index.upsert(vectors=records)

print("✅ 임베딩 및 Pinecone 업로드 완료!")
