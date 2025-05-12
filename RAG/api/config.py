import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 데이터베이스 연결 설정
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "zipup-db.cnkoy8gkiz2v.ap-southeast-2.rds.amazonaws.com"),
    'database': os.getenv("DB_NAME", "postgres"),
    'user': os.getenv("DB_USER", "teammate"),
    'password': os.getenv("DB_PASSWORD", "teampass123"),
    'port': os.getenv("DB_PORT", "5432")
}

# API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# JWT 설정
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "3600"))

# 인프라 유형 및 설명
INFRA_TYPES = [
    {"code": "traffic_subway", "name": "지하철역", "description": "대중교통 접근성"},
    {"code": "traffic_bus", "name": "버스정류장", "description": "버스 노선 접근성"},
    {"code": "life_mart", "name": "대형마트", "description": "쇼핑 및 생필품 구매"},
    {"code": "life_department_store", "name": "백화점", "description": "쇼핑 및 편의시설"},
    {"code": "life_convenience_store", "name": "편의점", "description": "생필품 및 간편식품"},
    {"code": "life_community_center", "name": "주민센터", "description": "행정 및 복지 서비스"},
    {"code": "life_daiso", "name": "다이소", "description": "생활용품 및 잡화"},
    {"code": "life_cafe", "name": "카페", "description": "휴식 및 업무 공간"},
    {"code": "life_park", "name": "공원", "description": "여가 및 산책 공간"},
    {"code": "life_post_office", "name": "우체국", "description": "우편 및 행정 서비스"},
    {"code": "life_healthjang", "name": "헬스장", "description": "건강 관리 및 운동 시설"},
    {"code": "health_hospital", "name": "병원", "description": "의료 서비스"},
    {"code": "health_pharmacy", "name": "약국", "description": "의약품 구매"},
    {"code": "play_cinema", "name": "영화관", "description": "문화 및 엔터테인먼트"},
    {"code": "play_pc_cafe", "name": "PC방", "description": "게임 및 인터넷"},
    {"code": "play_karaoke", "name": "노래방", "description": "엔터테인먼트"},
    {"code": "safety_police_station", "name": "파출소/경찰서", "description": "치안 및 안전"}
]

# 인프라별 세부 질문
INFRA_DETAIL_QUESTIONS = {
    "traffic_subway": ["선호하시는 노선(예: 2호선, 9호선)이 있나요?"],
    "traffic_bus": ["주변에 최소 몇 개 이상의 정류장이 있으면 좋으신가요?", "정류장까지 도보 몇 분 이내가 편하신가요?"],
    "life_mart": ["선호하는 마트 브랜드(이마트·롯데마트·홈플러스 등)가 있나요?", "마트까지 도보 몇 분 이내를 원하시나요?"],
    "life_department_store": ["선호하시는 백화점 브랜드(롯데·신세계·현대 등)가 있으신가요?", "백화점까지 도보 몇 분 이내를 선호하시나요?"],
    "life_convenience_store": ["선호하는 편의점 브랜드(CU·GS25·세븐일레븐 등)가 있나요?", "편의점까지 도보 몇 분 이내가 편하신가요?"],
    "life_community_center": ["주로 이용하실 주민센터 서비스(민원·복지 등)가 있나요?", "주민센터까지 도보 몇 분 이내를 선호하시나요?"],
    "life_daiso": ["다이소까지 도보 몇 분 이내를 원하시나요?"],
    "life_cafe": ["선호하는 카페 브랜드(스타벅스·이디야·개인카페 등)가 있으신가요?", "카페까지 도보 몇 분 이내가 편하신가요?"],
    "life_park": ["특정 공원(예: 올림픽공원, 한강공원)을 선호하시나요?", "공원까지 도보 몇 분 이내를 원하시나요?"],
    "life_post_office": ["우체국까지 도보 몇 분 이내를 원하시나요?"],
    "life_healthjang": ["24시간 운영하는 시설이 필요하신가요?", "PT나 그룹 수업이 있는 곳을 선호하시나요?"],
    "health_hospital": ["내과·치과·소아과 등 특정 과목을 제공하는 병원이 필요하신가요?", "병원까지 도보 몇 분 이내를 선호하시나요?"],
    "health_pharmacy": ["선호하는 약국 체인(예: 서울약국, 우리약국 등)이 있나요?", "약국까지 도보 몇 분 이내를 원하시나요?"],
    "play_cinema": ["선호하는 영화관 체인(CGV·메가박스·롯데시네마 등)이 있나요?", "IMAX·4DX 같은 특수관을 원하시나요?", "영화관까지 도보 몇 분 이내를 원하시나요?"],
    "play_pc_cafe": ["PC방까지 도보 몇 분 이내를 선호하시나요?"],
    "play_karaoke": ["코인 노래방 vs 일반 예약제 노래방 중 무엇을 선호하시나요?", "노래방까지 도보 몇 분 이내를 원하시나요?"],
    "safety_police_station": ["파출소까지 도보 몇 분 이내가 좋으신가요?"]
}

PROPERTY_FEATURE_QUESTIONS = [
    {
        "code": "size", 
        "question": "원하시는 방 크기가 있으신가요? (평수)",
        "options": ["5평 이하", "5~10평", "10~15평", "15~20평", "20평 이상", "상관없음"]
    },
    {
        "code": "floor", 
        "question": "선호하시는 층수가 있으신가요?",
        "options": ["저층(1-3층)", "중층(4-7층)", "고층(8층 이상)", "반지하 제외", "옥탑 제외", "상관없음"]
    },
    {
        "code": "heating", 
        "question": "선호하시는 난방 방식이 있으신가요?",
        "options": ["개별난방", "중앙난방", "지역난방", "상관없음"]
    },
    {
        "code": "parking", 
        "question": "주차 가능 여부가 중요하신가요?",
        "options": ["있음", "없음", "상관없음"]
    },
    {
        "code": "elevator", 
        "question": "엘리베이터 유무가 중요하신가요?",
        "options": ["있음", "없음", "상관없음"]
    },
    {
        "code": "direction", 
        "question": "선호하시는 방향이 있으신가요?",
        "options": ["남향", "동향", "서향", "북향", "남동향", "남서향", "북동향", "북서향", "상관없음"]
    }
]
