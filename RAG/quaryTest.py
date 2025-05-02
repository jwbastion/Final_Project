import os
import pandas as pd
from math import radians, cos, sin, asin
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

# 1. 환경변수 로드 및 초기화
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME")
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,
        metric="cosine",
        spec=ServerlessSpec(cloud=os.getenv("PINECONE_CLOUD"), region=os.getenv("PINECONE_REGION"))
    )
index = pc.Index(index_name)

# 2. 지하철역 데이터 로드 (위/경도)
station_df = pd.read_csv("Data/지하철(위경도).csv", encoding="utf-8")  # columns: station_name, lat, lng

# 3. haversine 함수 (거리 계산)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(a**0.5)

# 4. 가장 가까운 지하철역과 거리 계산 함수
def find_nearest_station(user_lat, user_lng):
    station_df['dist'] = station_df.apply(lambda r: haversine(user_lat, user_lng, r.lat, r.lng), axis=1)
    nearest = station_df.loc[station_df.dist.idxmin()]
    return nearest.station_name, nearest.dist

# 5. 사용자 입력 함수들
def ask_service_choice():
    print("원하는 서비스를 선택하세요:")
    print("1. 매물→가장 가까운 지하철역 소요시간 기반 추천")
    print("2. 현재 위치 반경 내 매물 추천")
    return input("선택: ").strip()

def ask_movement_choice():
    print("이동 방법 선택:")
    print("1. 도보 이동만\n2. 대중교통 이동\n3. 상관없음 (빠른 쪽 추천)")
    return input("선택: ").strip()

def ask_budget():
    rent = int(input("월세 최대 얼마까지? (만원): ").strip())
    deposit = int(input("보증금 최대 얼마까지? (만원): ").strip())
    maint = int(input("관리비 최대 얼마까지? (만원): ").strip())
    return rent, deposit, maint

# 6. 임베딩 생성 함수
def get_embedding(text):
    res = client.embeddings.create(model="text-embedding-ada-002", input=text)
    return res.data[0].embedding

# 7. 바운딩 박스 계산 함수
def bounding_box(user_lat, user_lng, radius_km):
    delta_lat = radius_km / 111
    delta_lng = radius_km / (111 * cos(radians(user_lat)))
    return user_lat - delta_lat, user_lat + delta_lat, user_lng - delta_lng, user_lng + delta_lng

# 8. 메인 챗봇 실행

def run_chatbot(user_lat, user_lng):
    service = ask_service_choice()
    conds = {'service': service}

    # 1번: 역 기준 소요시간 처리
    if service == '1':
        station, dist_km = find_nearest_station(user_lat, user_lng)
        print(f"가장 가까운 역: {station} (거리 약 {dist_km:.2f}km)")
        movement = ask_movement_choice()
        time_limit = int(input("매물→역 소요시간 최대(분): ").strip())
        conds.update({'station': station, 'movement': movement, 'time_limit': time_limit})
    # 2번: 반경 처리
    elif service == '2':
        radius_m = float(input("검색 반경(m) 입력: ").strip())
        conds['radius_km'] = radius_m / 1000
    else:
        print("잘못된 선택입니다.")
        return

    # 예산 입력
    print("\n[예산 조건 입력]")
    rent, deposit, maint = ask_budget()
    conds.update({'rent': rent, 'deposit': deposit, 'maint': maint})

    # 쿼리 문자열 생성 및 임베딩
    parts = [f"월세 {rent}만원", f"보증금 {deposit}만원", f"관리비 {maint}만원"]
    if service == '1':
        parts += [f"역: {conds['station']}", f"{conds['time_limit']}분 이내 이동({conds['movement']})"]
    else:
        parts.append(f"{conds['radius_km']}km 반경 내")
    query_str = ", ".join(parts)
    print(f"\n[쿼리 문자열] {query_str}")
    embedding = get_embedding(query_str)

    # 필터 설정
    filter_cond = {'rent': {'$lte': rent}, 'deposit': {'$lte': deposit}, 'maint': {'$lte': maint}}
    matches = []

    if service == '1':
        filter_cond['station'] = {'$eq': conds['station']}
        field = 'walk_time' if conds['movement'] == '1' else 'transit_time'
        filter_cond[field] = {'$lte': conds['time_limit']}
        # 단일 호출
        res = index.query(vector=embedding, top_k=5, include_metadata=True, filter=filter_cond)
        matches = res.matches
    else:
        # 바운딩 박스 메타 필터
        min_lat, max_lat, min_lng, max_lng = bounding_box(user_lat, user_lng, conds['radius_km'])
        filter_cond['lat'] = {'$gte': min_lat, '$lte': max_lat}
        filter_cond['lng'] = {'$gte': min_lng, '$lte': max_lng}
        # 먼저 후보 추출
        res = index.query(vector=embedding, top_k=50, include_metadata=True, filter=filter_cond)
        # 후처리: 실제 원형 반경 필터
        for m in res.matches:
            lat = m.metadata.get('lat')
            lng = m.metadata.get('lng')
            if haversine(user_lat, user_lng, lat, lng) <= conds['radius_km']:
                matches.append(m)
        # 유사도 내림차순 정렬 후 상위 5개
        matches = sorted(matches, key=lambda x: x.score, reverse=True)[:5]

    # 결과 출력
    print("\n[추천 매물 결과]")
    if not matches:
        print("조건에 맞는 매물이 없습니다.")
    for i, m in enumerate(matches, 1):
        md = m.metadata
        print(f"{i}. {md.get('address','주소 없음')} | 월세 {md.get('rent','?')}만 | 보증금 {md.get('deposit','?')}만 | 관리비 {md.get('maint','?')}만 | 평수 {md.get('size','?')}평 | 유사도: {m.score:.4f}")

# 9. 실행 예시
run_chatbot(37.4765, 126.9816)
