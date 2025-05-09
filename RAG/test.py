# ① pinecone 모듈에서 Pinecone 클래스 가져오기
from pinecone import Pinecone
import os
import pinecone
from openai import OpenAI

# ② 클라이언트 인스턴스 생성
client = Pinecone(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment=os.getenv("PINECONE_ENV")  # 예: "us-west1-gcp"
)

# ③ Index 객체 얻기
index = client.Index(os.getenv("PINECONE_INDEX_NAME"))

result = index.query(
    vector=[0.0]*1536,         # 더미 벡터
    top_k=1,
    include_metadata=True,
    filter={
        "address": {"$eq": "서울 동작구 상도동 361-141"}
    }
)

if result.matches:
    m = result.matches[0]
    print("ID:", m.id)
    print("Score:", m.score)
    print("Metadata:", m.metadata)
else:
    print("해당 주소가 없습니다.")