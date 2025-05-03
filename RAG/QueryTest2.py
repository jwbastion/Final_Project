import os
from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone
from math import radians, cos, sin, asin
import psycopg2

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

INFRA_QUESTIONS = {
    "infra_cafe": "카페가 가까이 있는 걸 어떻게 생각하시나요?",
    "infra_park": "공원이 근처에 있으면 좋으신가요?",
    "infra_mart": "마트나 편의점이 가까이 있는 걸 원하시나요?",
    "infra_hospital": "병원이 가까이 있으면 안심이 되시나요?",
    "infra_pc_cafe": "PC방이 가까우면 좋은가요?"
}

INFRA_TABLE_MAP = {
    "infra_cafe": "life_cafe",
    "infra_park": "life_park",
    "infra_mart": "life_mart",
    "infra_hospital": "health_hospital",
    "infra_pc_cafe": "play_pc_cafe",
}

def ask(prompt):
    return input(prompt + "\n> ").strip()

def parse_boolean_with_llm(user_msg):
    system_prompt = (
        "아래 사용자 응답이 해당 시설에 대해 긍정적인 반응이면 true, 아니면 false로만 응답해줘."
        " 예시: '좋아요', '있으면 좋죠', '네' → true / '상관없어요', '잘 모르겠어요' → false"
    )
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]
    )
    return res.choices[0].message.content.strip().lower() == "true"

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(a**0.5)

def get_pg_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT")
    )

def get_infra_score(user_lat, user_lng, selected_infras, conn):
    total_score = 0
    for key in selected_infras:
        table = INFRA_TABLE_MAP.get(key)
        if not table:
            continue
        query = f"SELECT latitude, longitude FROM {table}"
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            count = sum(1 for lat, lng in rows if haversine(user_lat, user_lng, lat, lng) <= 0.3)
            total_score += count
    return total_score

def run_cli_chat():
    user_conditions = {}

    radius = ask("매물 위치 기준을 알려주세요. 거리(m) 단위로 입력해주세요.")
    user_conditions["radius"] = int(radius)
    print(f"선택한 반경: {radius}m")

    user_conditions["rent"] = int(ask("월세는 얼마까지 괜찮으신가요?"))
    user_conditions["deposit"] = int(ask("보증금은 얼마까지 괜찮으신가요?"))
    user_conditions["maint"] = int(ask("관리비는 얼마까지 괜찮으신가요?"))

    print(f"예산 요약: 월세 {user_conditions['rent']}만 / 보증금 {user_conditions['deposit']}만 / 관리비 {user_conditions['maint']}만")

    selected_infras = []
    for key, question in INFRA_QUESTIONS.items():
        answer = ask(question)
        if parse_boolean_with_llm(answer):
            selected_infras.append(key)

    user_conditions["selected_infras"] = selected_infras
    print(f"선택된 인프라: {selected_infras}")

    conn = get_pg_connection()
    user_lat = 37.5055712636346
    user_lng = 126.941856308051

    filter_cond = {
        "rent": {"$lte": user_conditions["rent"]},
        "deposit": {"$lte": user_conditions["deposit"]},
        "maint": {"$lte": user_conditions["maint"]},
    }

    res = index.query(
        vector=[0.0]*1536,
        top_k=50,
        include_metadata=True,
        filter=filter_cond
    )

    matches = []
    for m in res.matches:
        md = m.metadata
        dist = haversine(user_lat, user_lng, md["lat"], md["lng"])
        if dist <= user_conditions["radius"] / 1000:
            infra_score = get_infra_score(md["lat"], md["lng"], selected_infras, conn)
            matches.append({
                "address": md.get("address", "주소 없음"),
                "rent": md.get("rent", 0),
                "deposit": md.get("deposit", 0),
                "infra_score": infra_score,
                "dist": dist
            })

    conn.close()
    matches = sorted(matches, key=lambda x: (x["infra_score"], -x["dist"]), reverse=True)[:5]

    print("\n추천 매물 결과:")
    for i, m in enumerate(matches, 1):
        print(f"{i}. {m['address']} | 월세 {m['rent']}만 | 보증금 {m['deposit']}만 | 인프라점수: {m['infra_score']:.2f} | 거리: {m['dist']:.2f}km")

if __name__ == "__main__":
    run_cli_chat()
