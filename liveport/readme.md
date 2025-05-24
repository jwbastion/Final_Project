# -*- coding: utf-8 -*-

liveport(통합)/
├── models/
│   ├── __init__.py
│   └── user_model.py
├── routes/
│   ├── __init__.py
│   ├── user_route.py
│   └── chatbot_route.py  # RAG의 api.py 내용 통합
├── services/
│   ├── __init__.py
│   ├── user_service.py
│   ├── auth_service.py  # 인증 관련 공통 함수
│   ├── chatbot_service.py  # RAG의 chatbot.py 통합
│   └── recommender_service.py  # RAG의 recommender.py 통합
├── utils/
│   ├── __init__.py
│   └── common_utils.py  # RAG의 utils.py 통합
├── config.py  # 통합된 설정 파일
├── app.py  # 통합된 애플리케이션 진입점
└── .env  # 통합된 환경 변수