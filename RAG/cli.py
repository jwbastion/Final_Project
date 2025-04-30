from transport import calculate_walk_time, calculate_transit_time, recommend_transport
from geo import find_nearest_station
from room import find_rooms_in_radius
from room import find_all_rooms
from functools import lru_cache
from geo import haversine


def ask_location():
    lat = float(input("위도 입력: ").strip())
    lng = float(input("경도 입력: ").strip())
    return lat, lng


def ask_service_choice():
    print("원하는 서비스를 선택하세요:")
    print("1. 현재 위치에서 가장 가까운 지하철역까지 거리/시간")
    print("2. 현재 위치 반경 내 매물 추천")
    return input("선택: ").strip()


def ask_movement_choice():
    print("이동 방법 선택:")
    print("1. 도보 이동만\n2. 대중교통 이동\n3. 상관없음 (빠른 쪽 추천)")
    return input("선택: ").strip()


def filter_rooms_by_budget(rooms, budget):
    result = []
    for room, time, mode in rooms:
        rent, deposit, maintenance = room[5], room[6], room[7]
        if rent <= budget['rent'] and deposit <= budget['deposit'] and maintenance <= budget['maintenance']:
            result.append((room, time, mode))
    return result

def filter_radius_rooms_by_budget(rooms, budget):
    result = []
    for room in rooms:
        rent, deposit, maintenance = room[6], room[7], room[8]
        if rent <= budget['max_rent'] and deposit <= budget['max_deposit'] and maintenance <= budget['max_maintenance']:
            result.append(room)
    return result


API_CALL_COUNT = 0
API_CALL_LIMIT = 20
TRANSIT_CALL_COUNT = 0
TRANSIT_CALL_LIMIT = 20

def cached_walk_time(room_lat, room_lng, station_lat, station_lng):
    global API_CALL_COUNT
    try:
        if API_CALL_COUNT < API_CALL_LIMIT:
            API_CALL_COUNT += 1
            return calculate_walk_time(room_lat, room_lng, station_lat, station_lng)
        else:
            raise Exception("API limit reached, fallback to estimate")
    except:
        dist_m = haversine(room_lat, room_lng, station_lat, station_lng)
        return round(dist_m / 60, 1)

def cached_transit_time(room_lat, room_lng, station_lat, station_lng):
    global TRANSIT_CALL_COUNT
    try:
        if TRANSIT_CALL_COUNT < TRANSIT_CALL_LIMIT:
            TRANSIT_CALL_COUNT += 1
            return calculate_transit_time(room_lat, room_lng, station_lat, station_lng)
        else:
            raise Exception("Transit API limit reached, fallback to estimate")
    except:
        dist_km = haversine(room_lat, room_lng, station_lat, station_lng) / 1000
        return round(dist_km / 20 * 60, 1)  # 20km/h 평균 대중교통 속도

def handle_transport_flow(user_lat, user_lng):
    station_name, station_lat, station_lng, distance = find_nearest_station(user_lat, user_lng)
    print(f"가장 가까운 지하철역: {station_name} (거리: {distance:.2f} km)")

    movement = ask_movement_choice()
    time_limit = int(input("몇 분 이내 매물을 원하시나요? > ").strip())

    rooms = find_all_rooms()
    filtered = []

    for room in rooms:
        try:
            room_lat, room_lng = room[0], room[1]

            if movement == "1":
                time = cached_walk_time(room_lat, room_lng, station_lat, station_lng)
                mode_label = "도보"
            elif movement == "2":
                time = cached_transit_time(room_lat, room_lng, station_lat, station_lng)
                mode_label = "대중교통"
            elif movement == "3":
                walk = cached_walk_time(room_lat, room_lng, station_lat, station_lng)
                transit = cached_transit_time(room_lat, room_lng, station_lat, station_lng)
                if walk is not None and (transit is None or walk <= transit):
                    time, mode_label = walk, "도보"
                elif transit is not None:
                    time, mode_label = transit, "대중교통"
                else:
                    continue
            else:
                print("잘못된 입력입니다.")
                return []

            if time is not None and time <= time_limit:
                filtered.append((room, time, mode_label))
        except Exception as e:
            print(f"계산 오류: {e}")
            continue

    print(f"{time_limit}분 이내 도달 가능한 매물 수: {len(filtered)}")

    if not filtered:
        print("조건에 맞는 매물이 없습니다.")
        return []

    return filtered



def handle_radius_flow(user_lat, user_lng):
    radius_m = float(input("검색 반경(m) 입력: ").strip())
    rooms = find_rooms_in_radius(user_lat, user_lng, radius_m)
    if rooms:
        print(f"반경 {radius_m:.0f}m 내 매물 {len(rooms)}건 발견")
        return rooms  
    else:
        print("해당 반경 내 매물이 없습니다.")
        return []