Docker 참고자료:https://wikidocs.net/225586
- vscode 확정 프로그램: Dev Containers, Docker 설치

PostgreSQL 참고자료: https://wikidocs.net/184222

카테고리	테이블명
생활편의시설	life_mart, life_cafe, life_park 등
오락시설	play_pc_cafe, play_karaoke, play_cinema
교통시설	traffic_bus, traffic_subway
안전시설	safety_police_station
의료시설	health_hospital, health_pharmacy
회원가입	users

# 데이터 베이스(관리자)
docker 실행 명령어(관리자): docker compose up --build

# 버전 관리(관리자자)
pip freeze > requirements.txt

# 1. 이거 꼭 해라 Docker server start
docker compose up --build