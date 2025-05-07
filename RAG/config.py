import os
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

db_config = {
    'host': os.getenv("POSTGRES_HOST", "zipup-db.cnkoy8gkiz2v.ap-southeast-2.rds.amazonaws.com"),
    'database': os.getenv("POSTGRES_DB", "postgres"),
    'user': os.getenv("POSTGRES_USER", "teammate"),
    'password': os.getenv("POSTGRES_PASSWORD", "teampass123"),
    'port': os.getenv("POSTGRES_PORT", "5432")
}

# 인프라 유형 및 설명 - 데이터베이스 테이블과 일치하도록 수정
INFRA_TYPES = [
    {"code": "traffic_subway", "name": "지하철역", "description": "대중교통 접근성"},
    {"code": "traffic_bus", "name": "버스정류장", "description": "버스 노선 접근성"},
    {"code": "life_mart", "name": "대형마트", "description": "쇼핑 및 생필품 구매"},
    {"code": "life_department", "name": "백화점", "description": "쇼핑 및 편의시설"},
    {"code": "life_park", "name": "공원", "description": "여가 및 산책 공간"},
    {"code": "life_cafe", "name": "카페", "description": "휴식 및 업무 공간"},
    {"code": "health_hospital", "name": "병원", "description": "의료 서비스"},
    {"code": "health_pharmacy", "name": "약국", "description": "의약품 구매"},
    {"code": "health_gym", "name": "헬스장", "description": "운동 및 건강 관리"},
    {"code": "play_cinema", "name": "영화관", "description": "문화 및 엔터테인먼트"},
    {"code": "play_golf", "name": "골프장", "description": "스포츠 및 레저"},
    {"code": "play_pc_cafe", "name": "PC방", "description": "게임 및 인터넷"},
    {"code": "play_karaoke", "name": "노래방", "description": "엔터테인먼트"},
    {"code": "play_facility", "name": "놀이시설", "description": "오락 및 여가"},
    {"code": "safety_police_station", "name": "경찰서/파출소", "description": "치안 및 안전"},
    {"code": "admin_post_office", "name": "우체국", "description": "우편 및 행정 서비스"}
]
