import openrouteservice
import requests
import os 
from dotenv import load_dotenv
from geo import haversine

load_dotenv()  # .env 파일 불러오기

ORS_API_KEY = os.getenv("ORS_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
ors_client = openrouteservice.Client(key=ORS_API_KEY)
ors_client = openrouteservice.Client(key=ORS_API_KEY)

def calculate_walk_time(origin_lat, origin_lng, dest_lat, dest_lng):
    coords = ((origin_lng, origin_lat), (dest_lng, dest_lat))
    try:
        result = ors_client.directions(coordinates=coords, profile='foot-walking', format='json')
        return result['routes'][0]['summary']['duration'] / 60
    except:
        # 실패하면 직선거리 기반으로 추정 시간 반환
        dist = haversine(origin_lat, origin_lng, dest_lat, dest_lng)
        return round(dist / 67, 1)

def calculate_transit_time(origin_lat, origin_lng, dest_lat, dest_lng):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"{origin_lat},{origin_lng}",
        "destination": f"{dest_lat},{dest_lng}",
        "mode": "transit",
        "key": GOOGLE_API_KEY
    }
    try:
        res = requests.get(url, params=params)
        data = res.json()
        if data["status"] == "OK":
            return data["routes"][0]["legs"][0]["duration"]["value"] / 60
    except:
        return None
    return None

def recommend_transport(user_lat, user_lng, station_lat, station_lng):
    walk_time = calculate_walk_time(user_lat, user_lng, station_lat, station_lng)
    transit_time = calculate_transit_time(user_lat, user_lng, station_lat, station_lng)
    if walk_time is not None and transit_time is not None:
        return ("walk", walk_time) if walk_time <= transit_time else ("transit", transit_time)
    if walk_time is not None:
        return ("walk", walk_time)
    if transit_time is not None:
        return ("transit", transit_time)
    return (None, None)