import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 설정
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "zipup-db.cnkoy8gkiz2v.ap-southeast-2.rds.amazonaws.com"),
    'database': os.getenv("DB_NAME", "postgres"),
    'user': os.getenv("DB_USER", "teammate"),
    'password': os.getenv("DB_PASSWORD", "teampass123"),
    'port': os.getenv("DB_PORT", "5432")
}

# API 키
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# LLM 모델 설정
LLM_MODEL = "gpt-3.5-turbo"

# 기본 상태 설정
DEFAULT_LAT = 37.5055712636346
DEFAULT_LNG = 126.941856308051
DEFAULT_RENT = 50
DEFAULT_DEPOSIT = 1000
DEFAULT_MAINT = 30