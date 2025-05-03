import os
import pandas as pd
import requests
from dotenv import load_dotenv
from geopy.distance import geodesic

# 1. 환경 변수 로드
load_dotenv()
ORS_API_KEY = os.getenv("ORS_API_KEY")

# 2. 데이터 로드
listings_df = pd.read_csv("Data.csv")
stations_df = pd.read_csv("지하철(위경도).csv")

# 3. 가장 가까운 지하철역 찾기
def find_nearest_station(lat, lng, station_df):
    station_df["거리"] = station_df.apply(
        lambda row: geodesic((lat, lng), (row["lat"], row["lng"])).meters,
        axis=1
    )
    nearest = station_df.sort_values("거리").iloc[0]
    return nearest["station_name"], nearest["lat"], nearest["lng"]

# 4. ORS 도보 소요시간 + fallback
def get_walk_time_ors(start_lng, start_lat, end_lng, end_lat):
    try:
        url = "https://api.openrouteservice.org/v2/directions/foot-walking"
        headers = {"Authorization": ORS_API_KEY, "Content-Type": "application/json"}
        coords = [[start_lng, start_lat], [end_lng, end_lat]]
        body = {"coordinates": coords}
        res = requests.post(url, json=body, headers=headers)
        res.raise_for_status()
        data = res.json()

        if "features" not in data or not data["features"]:
            raise ValueError("경로 없음")

        duration = data["features"][0]["properties"]["summary"]["duration"]
        return round(duration / 60)

    except Exception as e:
        dist_m = geodesic((start_lat, start_lng), (end_lat, end_lng)).meters
        fallback_min = round(dist_m / 67)
        print(f"⚠️ ORS 실패 fallback: 거리 {int(dist_m)}m → 도보 {fallback_min}분")
        return fallback_min

# 5. 결과 문장 생성
embed_sentences = []

for idx, row in listings_df.iterrows():
    lat, lng = row["위도"], row["경도"]
    station, st_lat, st_lng = find_nearest_station(lat, lng, stations_df)

    walk_min = get_walk_time_ors(lng, lat, st_lng, st_lat)

    sentence = f"{station}역까지 도보 약 {walk_min}분 소요"
    embed_sentences.append(sentence)

# 6. 결과 저장
listings_df["도보시간"] = embed_sentences
listings_df.to_csv("매물_도보시간포함.csv", index=False, encoding="utf-8-sig")
print("✅ 지하철 중심좌표 기반 도보시간 계산 완료: 매물_지하철도보시간포함.csv")
