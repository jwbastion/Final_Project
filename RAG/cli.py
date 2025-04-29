from transport import calculate_walk_time, calculate_transit_time, recommend_transport
from geo import find_nearest_station
from room import find_rooms_in_radius

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

def handle_transport_flow(user_lat, user_lng):
    station_name, station_lat, station_lng, distance = find_nearest_station(user_lat, user_lng)
    print(f"가장 가까운 지하철역: {station_name} (거리: {distance:.2f} km)")

    choice = ask_movement_choice()

    if choice == "1":
        walk_time = calculate_walk_time(user_lat, user_lng, station_lat, station_lng)
        if walk_time:
            print(f"도보 소요 시간: {walk_time:.2f}분")
        else:
            print("도보 경로를 찾을 수 없습니다.")
    elif choice == "2":
        transit_time = calculate_transit_time(user_lat, user_lng, station_lat, station_lng)
        if transit_time:
            print(f"대중교통 소요 시간: {transit_time:.2f}분")
        else:
            print("대중교통 경로를 찾을 수 없습니다.")
    elif choice == "3":
        mode, time = recommend_transport(user_lat, user_lng, station_lat, station_lng)
        if mode and time:
            mode_kor = "도보" if mode == "walk" else "대중교통"
            print(f"{mode_kor} 추천 ({time:.2f}분 소요)")
        else:
            print("추천할 이동 경로를 찾을 수 없습니다.")
    else:
        print("잘못된 입력입니다.")

def handle_radius_flow(user_lat, user_lng):
    radius_m = float(input("검색 반경(m) 입력: ").strip())
    rooms = find_rooms_in_radius(user_lat, user_lng, radius_m)
    if rooms:
        print(f"반경 {radius_m:.0f}m 내 매물 {len(rooms)}건 발견")
        for room in rooms:
            print(f"- {room[1]} / {room[2]} {room[3]} ({room[4]}) | 거리 {room[5]}m")
    else:
        print("해당 반경 내 매물이 없습니다.")