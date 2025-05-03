import os
import numpy as np
from math import radians, sin, cos, asin
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec
from sklearn.neighbors import BallTree
from preprocess.db_loader import load_infra_from_db, TABLES
from preprocess.infra_features import build_trees, find_nearest_tree, haversine

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
infra_dfs = load_infra_from_db()
build_trees(infra_dfs)

def ask(prompt):
    while True:
        resp = input(prompt).strip()
        if resp:
            return resp

def ask_int(prompt):
    while True:
        resp = ask(prompt)
        if resp.isdigit():
            return int(resp)

def run_chatbot():
    while True:
        if ask("exit 입력 시 종료, 계속하려면 엔터: ").lower() == 'exit':
            break
        user_lat = float(ask("위도: "))
        user_lng = float(ask("경도: "))
        rent = ask_int("월세 최대 (만원): ")
        deposit = ask_int("보증금 최대 (만원): ")
        maint = ask_int("관리비 최대 (만원): ")
        theme_map = {
            1: ['life_convenience_store','life_mart','life_cafe','life_park','life_post_office','life_department_store','life_daiso','life_community_center'],
            2: ['traffic_subway','traffic_bus'],
            3: ['health_hospital','health_pharmacy'],
            4: ['play_cinema','play_pc_cafe','play_karaoke'],
            5: ['safety_police_station','officetels']
        }
        print("1) 집 근처 편의  2) 교통  3) 의료  4) 여가  5) 안전")
        scenario = ask_int("선택 (1-5): ")
        subs = theme_map.get(scenario, [])
        for i, tbl in enumerate(subs, 1):
            print(f"{i}) {tbl}")
        chosen_tbl = subs[ask_int("선택 번호: ") - 1]
        row, dist_m = find_nearest_tree(chosen_tbl, user_lat, user_lng)
        print(f"{chosen_tbl} 거리: {int(dist_m)}m")
        max_dist = int(dist_m) if ask("만족? (y/n): ").lower().startswith('y') else ask_int("허용 거리 (m): ")
        parts = [f"위치({user_lat},{user_lng})", f"월세≤{rent}", f"보증금≤{deposit}", f"관리비≤{maint}", f"{chosen_tbl}≤{max_dist}m"]
        embedding = client.embeddings.create(model="text-embedding-ada-002", input=", ".join(parts)).data[0].embedding
        infra_station = row['business_name']
        filter_cond = {
            'rent': {'$lte': rent},
            'deposit': {'$lte': deposit},
            'maint': {'$lte': maint},
            'station': {'$eq': infra_station}
        }
        res = index.query(vector=embedding, top_k=100, include_metadata=True, filter=filter_cond)
        candidates = res.matches
        filtered = []
        for m in candidates:
            lat = m.metadata['lat']
            lng = m.metadata['lng']
            dist_m2 = haversine(user_lat, user_lng, lat, lng) * 1000
            if scenario == 2:
                t = m.metadata['walk_time']
                if t <= maint and dist_m2 <= max_dist:
                    filtered.append((m, dist_m2))
            else:
                if dist_m2 <= max_dist:
                    filtered.append((m, dist_m2))
        filtered.sort(key=lambda x: x[0].score, reverse=True)
        matches = [m for m, _ in filtered[:5]]
        if not matches:
            print("조건에 맞는 매물이 없습니다.")
        else:
            for i, m in enumerate(matches, 1):
                md = m.metadata
                dist = int(haversine(user_lat, user_lng, md['lat'], md['lng']) * 1000)
                print(f"{i}. {md['address']} | 월세 {md['rent']}만 | 보증금 {md['deposit']}만 | 거리 {dist}m")

if __name__ == '__main__':
    run_chatbot()