import pandas as pd
import numpy as np
import faiss
import re
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
df = pd.read_pickle("./vectorEmbeding/매물_db.pkl")

def parse_query(query):
    cond = {}

    keyword_map = {
        "투룸": ("type", "투룸"),
        "원룸": ("type", "원룸"),
        "치안": ("safety_수_min", 2),
        "생활편의": ("life_수_min", 5),
        "편의점": ("life_수_min", 5),
        "마트": ("life_수_min", 5),
        "병원": ("health_care_수_min", 5),
        "의료": ("health_care_수_min", 5),
        "헬스": ("health_수_min", 3),
        "운동": ("health_수_min", 3),
        "여가": ("play_수_min", 3),
        "노래방": ("play_수_min", 3),
        "영화관": ("play_수_min", 3),
        "교통": ("traffic_수_min", 3),
        "역세권": ("traffic_수_min", 3),
    }

    for word, (key, val) in keyword_map.items():
        if word in query:
            cond[key] = val

    price_patterns = {
        "월세": "월세(만원)_max",
        "보증금": "보증금(만원)_max",
        "관리비": "관리비(만원)_max"
    }

    for word, key in price_patterns.items():
        match = re.search(fr"{word}\s?(\d+)", query)
        if match:
            cond[key] = int(match.group(1))

    match_min = re.search(r"(\d+)평\s?이상", query)
    if match_min:
        cond["평수_min"] = int(match_min.group(1))

    match_max = re.search(r"(\d+)평\s?이하", query)
    if match_max:
        cond["평수_max"] = int(match_max.group(1))

    match_gu = re.search(r"(강남구|강동구|강북구|강서구|관악구|광진구|구로구|금천구|노원구|도봉구|동대문구|동작구|마포구|서대문구|서초구|성동구|성북구|송파구|양천구|영등포구|용산구|은평구|종로구|중구|중랑구)", query)
    if match_gu:
        cond["자치구"] = match_gu.group(1)

    if re.search(r"(가장\s*싼|제일\s*싼|저렴한|가성비)", query):
        cond["sort_by"] = "월세(만원)"
        cond["sort_order"] = "asc"

    if re.search(r"(넓은|큰 평수|큰 집)", query):
        cond["sort_by"] = "평수"
        cond["sort_order"] = "desc"

    return cond

def apply_filters(df, cond):
    numeric_ops = {
        "_min": lambda d, col, val: d[d[col] >= val],
        "_max": lambda d, col, val: d[d[col] <= val]
    }

    for key, value in cond.items():
        if key == "type":
            df = df[df["type"] == value]
        elif key == "자치구":
            df = df[df["자치구"].str.contains(value)]
        else:
            for suffix, op in numeric_ops.items():
                if key.endswith(suffix):
                    col = key.replace(suffix, "")
                    df = op(df, col, value)
                    break
    return df

def recommend(query):
    cond = parse_query(query)
    filtered_df = apply_filters(df.copy(), cond)
    filtered_df["가성비"] = filtered_df["평수"] / (filtered_df["월세(만원)"] + 1)

    texts = filtered_df["text"].tolist()
    vectors = np.array(filtered_df["embedding"].tolist()).astype("float32")

    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)

    query_vec = model.encode([query])
    _, indices = index.search(np.array(query_vec), k=3)

    top_texts = [texts[i] for i in indices[0]]
    context = "\n".join([f"{i+1}. {t}" for i, t in enumerate(top_texts)])

    prompt = f"""
    사용자가 "{query}"라고 요청했을 때, 아래 매물 중 최대 3개를 추천해줘.
    각 매물에 대해 추천 이유도 자연스럽게 말해줘.

    참고로, 아래 수치는 점수가 아니라 거리 기반 인프라 수입니다.
    각 항목은 매물 반경 내 인프라 개수를 의미하며, 하버사인 거리 기준으로 다음과 같이 계산되었습니다:

    - 교통 (traffic): 반경 250m 이내 지하철역 + 버스정류장 수
    - 생활편의 (life): 반경 200m 이내 마트, 카페, 편의점 등
    - 건강 (health): 반경 300m 이내 헬스장, 체육시설 등
    - 의료 (health_care): 반경 400m 이내 병원, 약국 등
    - 여가 (play): 반경 300m 이내 영화관, 노래방, PC방 등
    - 치안 (safety): 반경 500m 이내 파출소 수

    점수로 착각하지 말고, 예를 들어 '치안 점수 2점'이 아닌 '파출소 2개 있음'처럼 표현해주세요.

    {context}
    """


    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 부동산 매물 추천 전문가입니다."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def print_recommendations(result_text):
    print("\n추천 결과")
    items = result_text.strip().split("\n\n")
    for i, block in enumerate(items, 1):
        block = re.sub(r"^\d+\.\s*", "", block.strip())
        print(f"\n매물 {i}\n{block}\n{'-'*50}")


while True:
    user_input = input("사용자: ")
    if user_input.lower() in ['exit', 'quit', 'q']:
        break
    result = recommend(user_input)
    print_recommendations(result)