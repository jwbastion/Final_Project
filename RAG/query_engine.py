import os
import psycopg2
import pandas as pd
from pinecone import Pinecone
from math import radians, cos, sin, asin
from dotenv import load_dotenv

# .env 경로 명시적으로 로드
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

INFRA_TABLE_MAP = {
    "infra_cafe": "life_cafe",
    "infra_park": "life_park",
    "infra_mart": "life_mart",
    "infra_hospital": "health_hospital",
    "infra_pharmacy": "health_pharmacy",
    "infra_cinema": "play_cinema",
    "infra_karaoke": "play_karaoke",
    "infra_pc_cafe": "play_pc_cafe",
    "infra_police": "safety_police_station",
    "infra_subway": "traffic_subway",
    "infra_bus": "traffic_bus"
}

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(a**0.5)

def get_pg_connection():
    print("CONNECT TO DB:", {
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT")
    })

    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )

def get_infra_score(user_lat, user_lng, selected_infras):
    conn = get_pg_connection()
    total_score = 0

    for key in selected_infras:
        table = INFRA_TABLE_MAP.get(key)
        if not table:
            continue

        query = f"SELECT latitude, longitude FROM {table}"
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            count = 0
            for lat, lng in rows:
                if haversine(user_lat, user_lng, lat, lng) <= 0.3:  # 0.3km = 300m
                    count += 1
            total_score += count

    conn.close()
    return total_score


def run_query_mode(user_lat, user_lng, conds):
    rent, deposit, maint = conds["rent"], conds["deposit"], conds["maint"]

    filter_cond = {
        "rent": {"$lte": rent},
        "deposit": {"$lte": deposit},
        "maint": {"$lte": maint}
    }

    res = index.query(
        vector=[0.0] * 1536,
        top_k=50,
        include_metadata=True,
        filter=filter_cond
    )

    movement_field = "walk_time" if conds.get("movement") == "walk" else "transit_time"
    time_limit = conds.get("time_limit", 999)
    selected_infras = conds.get("selected_infras", [])

    matches = []
    for m in res.matches:
        md = m.metadata
        if md.get(movement_field, 999) > time_limit:
            continue
        infra_score = get_infra_score(md["lat"], md["lng"], selected_infras)
        matches.append({
            "address": md.get("address", "주소 없음"),
            "rent": md.get("rent", 0),
            "deposit": md.get("deposit", 0),
            "infra_score": infra_score,
            "score": m.score
        })

    matches = sorted(matches, key=lambda x: (x["infra_score"], x["score"]), reverse=True)[:5]
    return matches