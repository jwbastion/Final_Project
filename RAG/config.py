import os
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

db_config = {
    'host': os.getenv("DB_HOST", "localhost"),
    'database': os.getenv("DB_NAME", "mydb"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", "1234"),
    'port': os.getenv("DB_PORT", "5432")
}

# 인프라 유형 및 설명
INFRA_TYPES = [
    {"code": "subway", "name": "지하철역", "description": "대중교통 접근성"},
    {"code": "bus", "name": "버스정류장", "description": "버스 노선 접근성"},
    {"code": "bigmart", "name": "대형마트", "description": "쇼핑 및 생필품 구매"},
    {"code": "department_store", "name": "백화점", "description": "쇼핑 및 편의시설"},
    {"code": "park", "name": "공원", "description": "여가 및 산책 공간"},
    {"code": "health", "name": "헬스장/의료시설", "description": "건강 및 의료 서비스"},
    {"code": "cinema", "name": "영화관", "description": "문화 및 엔터테인먼트"},
    {"code": "golf", "name": "골프장", "description": "스포츠 및 레저"},
    {"code": "pc", "name": "PC방", "description": "게임 및 인터넷"},
    {"code": "play", "name": "놀이시설", "description": "오락 및 여가"},
    {"code": "police", "name": "경찰서", "description": "치안 및 안전"},
    {"code": "post_office", "name": "우체국", "description": "우편 및 행정 서비스"},
    {"code": "sing", "name": "노래방", "description": "엔터테인먼트"}
]
