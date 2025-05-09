chatbot/
├── app.py                 # Flask 애플리케이션 진입점
├── config.py              # 환경 설정 및 상수
├── requirements.txt       # 필요한 패키지 목록
├── static/                # 정적 파일 (CSS, JS, 이미지)
│   └── images/            # 이미지 리소스
├── templates/             # HTML 템플릿
│   └── index.html         # 메인 챗봇 인터페이스
├── models/                # 데이터 모델
│   ├── __init__.py
│   ├── infra_types.py     # 인프라 유형 및 질문 데이터
│   └── user_state.py      # 사용자 상태 관리
├── services/              # 핵심 서비스
│   ├── __init__.py
│   ├── db_service.py      # 데이터베이스 연결 및 쿼리
│   ├── vector_service.py  # Pinecone 벡터 검색
│   ├── llm_service.py     # OpenAI LLM 서비스
│   └── recommender.py     # 매물 추천 엔진
├── utils/                 # 유틸리티 함수
│   ├── __init__.py
│   ├── distance.py        # 거리 계산 함수
│   └── formatter.py       # 출력 포맷팅 유틸리티
└── chatbot/               # 챗봇 로직
    ├── __init__.py
    └── chatbot.py         # 메인 챗봇 클래스