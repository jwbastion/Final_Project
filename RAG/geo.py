import math
from db import connect_db

def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def find_nearest_station(user_lat, user_lng):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT station_name, lat, lng FROM subway_stations;")
    stations = cur.fetchall()
    cur.close()
    conn.close()
    nearest = min(stations, key=lambda s: haversine(user_lat, user_lng, s[1], s[2]))
    return nearest[0], nearest[1], nearest[2], haversine(user_lat, user_lng, nearest[1], nearest[2]) / 1000
