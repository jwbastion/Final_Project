import json

# JSON 데이터 로딩
with open("gobang_api.json", "r", encoding="utf-8") as f:
    houses = json.load(f)

essential_fields = [
    "ID",
    "ADDR_FULL_BUNJI",
    "HOUSE_TYPE_NM",
    "FLOOR",
    "PRICE_MIN",
    "PRICE_MAX",
    "DEPOSIT_MIN",
    "DEPOSIT_MAX",
    "MAINTENANCE_FEE",
    "GENDER_TYPE_NM",
    "DURATION_MIN",
    "nearSubways",
    "LATITUDE",
    "LONGITUDE",
    "면적",
    "주실 방향",
    "주차",
    "난방시설",
    "냉방시설",
    "생활시설",
    "안전시설",
    "엘리베이터",
]

# 필터링된 데이터 생성
filtered_data = {}
for house in houses:
    name = house.get("NAME", "UNKNOWN")
    entry = {key: house.get(key) for key in essential_fields}

    tags = house.get("TAGS")
    type = house.get("HOUSE_TYPE_NMS")
    if type == "원･투룸":
        if "원룸" in tags:
            entry["HOUSE_TYPE_NM"] = "원룸"
        else:
            entry["HOUSE_TYPE_NM"] = "투룸"

    # 지하철 정보 처리
    if entry["nearSubways"] and entry["nearSubways"][0]:
        subway_info = entry["nearSubways"][0][0]
        entry["지하철역"] = subway_info.get("NAME")
        entry["호선"] = subway_info.get("LINE_SHORT")
        entry["역까지거리(km)"] = round(float(subway_info.get("distance", 0)), 2)
    else:
        entry["지하철역"] = None
        entry["호선"] = None
        entry["역까지거리(km)"] = None

    # 제거
    del entry["nearSubways"]

    filtered_data[name] = entry

# JSON으로 저장
output_path = "filtered_output.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(filtered_data, f, indent=2, ensure_ascii=False)
