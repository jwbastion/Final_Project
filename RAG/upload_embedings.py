import os
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

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
df = pd.read_csv("Data.csv", encoding="utf-8")

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

# 6. OpenAI 임베딩 + Pinecone 업서트
batch_size = 50
records = []
for i, row in df.iterrows():
    try:
        res = client.embeddings.create(
            model="text-embedding-ada-002",
            input=row["embed_text"]
        )
        embedding = res.data[0].embedding

        meta = row.to_dict()  

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
