# config.py 전체 코드

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
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION"))

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

# 새로운 구조화된 세부 질문 (꼬리 질문 형태)
INFRA_DETAIL_QUESTIONS_V2 = {
    # 공통 질문 (모든 인프라 유형에 적용)
    "common_questions": {
        "importance": "이 시설이 얼마나 중요한가요? (1: 별로 중요하지 않음 ~ 5: 매우 중요함)",
        "distance": "이 시설까지 도보 몇 분 이내가 좋으신가요? (숫자만 입력해주세요)",
        "frequency": "이 시설을 얼마나 자주 이용하실 계획인가요? (1: 거의 이용 안함 ~ 5: 거의 매일)"
    },
    
    # 인프라별 고유 질문 (인프라별 특화 질문 1개씩)
    "specific_questions": {
        "traffic_subway": {
            "preferred_line": "선호하시는 지하철 노선이 있나요? (예: 2호선, 9호선)"
        },
        "traffic_bus": {
            "route_types": "시내버스, 광역버스, 마을버스 중 주로 이용하는 유형은 무엇인가요?"
        },
        "life_mart": {
            "preferred_brand": "선호하는 마트 브랜드가 있나요? (예: 이마트, 롯데마트, 홈플러스)"
        },
        "life_department_store": {
            "preferred_brand": "선호하시는 백화점 브랜드가 있으신가요? (예: 롯데, 신세계, 현대)"
        },
        "life_convenience_store": {
            "preferred_brand": "선호하는 편의점 브랜드가 있나요? (예: CU, GS25, 세븐일레븐)"
        },
        "life_cafe": {
            "preferred_brand": "선호하는 카페 브랜드가 있으신가요? (예: 스타벅스, 이디야, 투썸플레이스)"
        },
        "life_park": {
            "features": "공원에서 주로 어떤 활동을 하실 계획인가요? (산책, 운동, 피크닉 등)"
        },
        "life_healthjang": {
            "hours": "24시간 운영하는 시설이 필요하신가요? (예/아니오)"
        },
        "health_hospital": {
            "specialty": "주로 찾으실 병원 유형이 있나요? (내과, 치과, 소아과 등)"
        },
        "health_pharmacy": {
            "hours": "야간에도 운영하는 약국이 필요하신가요? (예/아니오)"
        },
        "play_cinema": {
            "preferred_brand": "선호하는 영화관 체인이 있나요? (예: CGV, 메가박스, 롯데시네마)"
        },
        "play_karaoke": {
            "type": "코인 노래방과 일반 예약제 노래방 중 어떤 것을 선호하시나요?"
        },
        "safety_police_station": {
            "importance_reason": "안전에 관련하여 특별히 신경 쓰시는 부분이 있으신가요?"
        },
        "life_community_center": {
            "services": "주로 이용하실 주민센터 서비스가 있나요? (민원, 복지 등)"
        },
        "life_daiso": {
            "items": "다이소에서 주로 구매하시는 품목이 무엇인가요?"
        },
        "life_post_office": {
            "services": "우체국에서 주로 이용하시는 서비스가 무엇인가요? (우편물 발송, 예금 등)"
        },
        "play_pc_cafe": {
            "usage": "PC방을 주로 어떤 용도로 이용하시나요? (게임, 작업 등)"
        }
    }
}

PROPERTY_FEATURE_QUESTIONS = [
    {
        "code": "type", 
        "question": "선호하시는 주거 타입이 있으신가요?",
        "options": ["원룸", "투룸", "상관없음"]
    },
    
    {
        "code": "floor", 
        "question": "선호하시는 층수가 있으신가요?",
        "options": ["저층(1-3층)", "중층(4-7층)", "고층(8층 이상)", "반지하 제외", "옥탑 제외", "상관없음"]
    },
    
    {
        "code": "size", 
        "question": "원하시는 방 크기가 있으신가요? (평수)",
        "options": ["5평 이하", "5~10평", "10~15평", "15~20평", "20평 이상", "상관없음"]
    },
    
    {
        "code": "direction", 
        "question": "선호하시는 방향이 있으신가요?",
        "options": ["남향", "남동향", "동향", "남서향", "서향", "북동향", "북서향", "북향", "상관없음"]
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
    }
]

# 인프라 거리별 점수 가중치 정의
INFRA_DISTANCE_WEIGHTS = {
    # 지하철역 (중요도 높음)
    'traffic_subway': {
        'distance_ranges': [
            {'max': 500, 'score': 5.0},    # 500m 이내: 5점
            {'max': 1000, 'score': 4.0},   # 500m~1000m: 4점
            {'max': 1500, 'score': 3.0},   # 1000m~1500m: 3점
            {'max': 2000, 'score': 2.0},   # 1500m~2000m: 2점
            {'max': 3000, 'score': 1.0},   # 2000m~3000m: 1점
            {'max': float('inf'), 'score': 0.5}  # 3000m 초과: 0.5점
        ],
        'weight': 2.0  # 지하철은 중요도 2배
    },
    # 버스정류장
    'traffic_bus': {
        'distance_ranges': [
            {'max': 300, 'score': 5.0},    # 300m 이내: 5점
            {'max': 500, 'score': 4.0},    # 300m~500m: 4점
            {'max': 800, 'score': 3.0},    # 500m~800m: 3점
            {'max': 1200, 'score': 2.0},   # 800m~1200m: 2점
            {'max': 2000, 'score': 1.0},   # 1200m~2000m: 1점
            {'max': float('inf'), 'score': 0.5}  # 2000m 초과: 0.5점
        ],
        'weight': 1.5
    },
    # 대형마트
    'life_mart': {
        'distance_ranges': [
            {'max': 500, 'score': 5.0},  
            {'max': 1000, 'score': 4.0},  
            {'max': 1500, 'score': 3.0},   
            {'max': 2000, 'score': 2.0},  
            {'max': 3000, 'score': 1.0},   
            {'max': float('inf'), 'score': 0.5}
        ],
        'weight': 1.5
    },
    # 편의점
    'life_convenience_store': {
        'distance_ranges': [
            {'max': 200, 'score': 5.0},
            {'max': 400, 'score': 4.0},
            {'max': 600, 'score': 3.0},
            {'max': 800, 'score': 2.0},
            {'max': 1000, 'score': 1.0},
            {'max': float('inf'), 'score': 0.5}
        ],
        'weight': 1.0
    },
    # 카페
    'life_cafe': {
        'distance_ranges': [
            {'max': 300, 'score': 5.0},
            {'max': 500, 'score': 4.0},
            {'max': 700, 'score': 3.0},
            {'max': 1000, 'score': 2.0},
            {'max': 1500, 'score': 1.0},
            {'max': float('inf'), 'score': 0.5}
        ],
        'weight': 1.0
    },
    # 헬스장
    'life_healthjang': {
        'distance_ranges': [
            {'max': 300, 'score': 5.0},
            {'max': 500, 'score': 4.0},
            {'max': 800, 'score': 3.0},
            {'max': 1200, 'score': 2.0},
            {'max': 2000, 'score': 1.0},
            {'max': float('inf'), 'score': 0.5}
        ],
        'weight': 1.0
    },
    # 병원
    'health_hospital': {
        'distance_ranges': [
            {'max': 500, 'score': 5.0},
            {'max': 1000, 'score': 4.0},
            {'max': 1500, 'score': 3.0},
            {'max': 2000, 'score': 2.0},
            {'max': 3000, 'score': 1.0},
            {'max': float('inf'), 'score': 0.5}
        ],
        'weight': 1.2
    },
    # 약국
    'health_pharmacy': {
        'distance_ranges': [
            {'max': 300, 'score': 5.0},
            {'max': 600, 'score': 4.0},
            {'max': 1000, 'score': 3.0},
            {'max': 1500, 'score': 2.0},
            {'max': 2000, 'score': 1.0},
            {'max': float('inf'), 'score': 0.5}
        ],
        'weight': 1.2
    },
    # 공원
    'life_park': {
        'distance_ranges': [
            {'max': 500, 'score': 5.0},
            {'max': 1000, 'score': 4.0},
            {'max': 1500, 'score': 3.0},
            {'max': 2000, 'score': 2.0},
            {'max': 3000, 'score': 1.0},
            {'max': float('inf'), 'score': 0.5}
        ],
        'weight': 1.0
    },
    # 기본 가중치 (다른 모든 인프라에 적용)
    'default': {
        'distance_ranges': [
            {'max': 300, 'score': 5.0},
            {'max': 600, 'score': 4.0},
            {'max': 1000, 'score': 3.0},
            {'max': 1500, 'score': 2.0},
            {'max': 2500, 'score': 1.0},
            {'max': float('inf'), 'score': 0.5}
        ],
        'weight': 1.0
    }
}

# 인프라 카테고리 가중치 (인프라 유형별 중요도)
INFRA_CATEGORY_WEIGHTS = {
    'traffic_subway': 2.0,      # 지하철역
    'traffic_bus': 1.5,         # 버스 정류장
    'life_mart': 1.5,           # 대형마트
    'life_department_store': 1.2, # 백화점
    'life_convenience_store': 1.0, # 편의점
    'life_community_center': 0.8, # 주민센터
    'life_daiso': 0.7,          # 다이소
    'life_cafe': 1.0,           # 카페
    'life_park': 1.2,           # 공원
    'life_post_office': 0.7,    # 우체국
    'life_healthjang': 1.0,     # 헬스장
    'health_hospital': 1.2,     # 병원
    'health_pharmacy': 1.2,     # 약국
    'play_cinema': 0.8,         # 영화관
    'play_pc_cafe': 0.6,        # PC방
    'play_karaoke': 0.6,        # 노래방
    'safety_police_station': 1.0, # 파출소/경찰서
    'default': 0.8              # 기타 인프라
}

# 인프라 다양성 보너스 (다양한 인프라가 있을 때 추가 점수)
INFRA_DIVERSITY_BONUS = {
    3: 0.2,  # 3개 유형의 인프라: +0.2
    5: 0.5,  # 5개 유형의 인프라: +0.5
    7: 0.8,  # 7개 이상 유형의 인프라: +0.8
}