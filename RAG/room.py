from db import connect_db
from geo import haversine

def find_rooms_in_radius(user_lat, user_lng, radius_m):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT id, type, district, legal_dong, jibun_address, lat, lng FROM room_data;")
    results = []
    for row in cur.fetchall():
        id_, type_, district, dong, address, lat, lng = row
        distance_m = haversine(user_lat, user_lng, lat, lng)
        if distance_m <= radius_m:
            results.append((id_, type_, district, dong, address, int(distance_m)))
    cur.close()
    conn.close()
    return sorted(results, key=lambda x: x[5])