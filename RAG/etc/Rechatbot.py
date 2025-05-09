import os
import math
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

# 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc = pc = pc = pc # Fixing index instantiation
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

# 초기 설문 결과 기반 설정 (기본값)
user_state = {
    "lat": 37.5055712636346,
    "lng": 126.941856308051,
    "service": None,
    "movement": None,
    "time_limit": None,
    "radius": None,
    "rent": 50,
    "deposit": 1000,
    "maint": 30
}

# 코어 로직 시작

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# -- 검색 함수 정의 --
def search_by_location():
    resp = index.query(vector=[0.0]*1536, top_k=500, include_metadata=True)
    matches = resp.matches
    lat0, lng0 = user_state["lat"], user_state["lng"]

    if user_state["service"] == "1":
        # 소요시간 기준
        station_coords = {}
        for m in matches:
            md = m.metadata
            st, lat, lng = md.get("station"), md.get("lat"), md.get("lng")
            if st and isinstance(lat, float) and isinstance(lng, float):
                station_coords.setdefault(st, []).append((lat, lng))
        for st, coords in station_coords.items():
            lats = [c[0] for c in coords]
            lngs = [c[1] for c in coords]
            station_coords[st] = {"lat": sum(lats)/len(lats), "lng": sum(lngs)/len(lngs)}

        dist_list = [(st, haversine(lat0, lng0, c["lat"], c["lng"])) for st, c in station_coords.items()]
        dist_list.sort(key=lambda x: x[1])
        nearest = [st for st, _ in dist_list[:3]]

        key = "walk_time" if user_state["movement"] == "1" else "transit_time"
        filtered = [m for m in matches if m.metadata.get("station") in nearest and m.metadata.get(key) <= user_state["time_limit"]]
        filtered.sort(key=lambda m: m.metadata.get(key, 9999))
        return filtered[:5]
    elif user_state["service"] == "2":
        # 반경 기준
        rad = user_state["radius"]
        filtered = [m for m in matches if isinstance(m.metadata.get("lat"), float)
                    and isinstance(m.metadata.get("lng"), float)
                    and haversine(lat0, lng0, m.metadata["lat"], m.metadata["lng"]) <= rad]
        filtered.sort(key=lambda m: haversine(lat0, lng0, m.metadata.get("lat", lat0), m.metadata.get("lng", lng0)))
        return filtered[:10]
    # 상관없음 포함
    return []


def search_by_budget():
    result = index.query(vector=[0.0]*1536, top_k=500, include_metadata=True)
    filtered = [m for m in result.matches if m.metadata.get('rent',9999) <= user_state['rent']
                and m.metadata.get('deposit',99999) <= user_state['deposit']
                and m.metadata.get('maint',9999) <= user_state['maint']]
    return filtered[:5]

# -- 결과 출력 헬퍼 --
def format_time(md, mov):
    walk = md.get("walk_time", 9999)
    trans = md.get("transit_time", 9999)
    if mov == "1": return f"도보 {walk}분"
    if mov == "2": return f"대중교통 {trans}분"
    t, mode = (walk, "도보") if walk <= trans else (trans, "대중교통")
    return f"{mode} {t}분"


def print_section(title, items, mov):
    if not items:
        print(f"{title}: 없음\n")
        return
    print(f"**{title} ({min(len(items),5)}건)**")
    for i, m in enumerate(items[:5], 1):
        md = m.metadata
        print(f"{i}. {md.get('address')} ({md.get('station')}) — 월세 {md.get('rent')}만, 보증금 {md.get('deposit')}만, 관리비 {md.get('maint')}만, {format_time(md, mov)}")
    print()

# -- 사용자 입력 처리 & 흐름 실행 --
budget_names = {'rent':'월세', 'deposit':'보증금', 'maint':'관리비'}
for key in budget_names:
    cur = user_state[key]
    print(f"현재 설정하신 {budget_names[key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
    ui = input("🙋 사용자: ").strip()
    if ui and ui != '없음':
        num = ''.join(filter(str.isdigit, ui))
        if num:
            user_state[key] = int(num)

print("어떤 기준으로 추천할까요?\n1. 소요시간 기준\n2. 반경 기준 (m 단위)\n3. 상관없음")
user_state['service'] = input("🙋 사용자: ").strip()
if user_state['service'] == '1':
    print("이동 방법? 1.도보 2.대중교통 3.상관없음")
    user_state['movement'] = input("🙋 사용자: ").strip()
    print("최대 소요시간(분)?")
    user_state['time_limit'] = int(input("🙋 사용자: ").strip())
elif user_state['service'] == '2':
    print("반경(m)을 입력하세요")
    user_state['radius'] = int(input("🙋 사용자: ").strip())
else:
    # 상관없음: movement 3 기본 처리
    user_state['movement'] = '3'

# 검색 및 출력
loc_matches = search_by_location()
bud_matches = search_by_budget()

print("\n🤖 추천 결과:")
print_section("거주지 기준 매물", loc_matches, user_state['movement'])
print_section("예산 기준 매물", bud_matches, user_state['movement'])
