"""
RAG 기반 부동산 추천 챗봇 (거주지/예산 기준 분리 + GPT 요약)
- 조건 입력 후:
  - 거주지 기준 (소요시간 또는 반경)
  - 예산 기준
- 두 결과를 GPT에게 넘겨서 자연어 요약 생성
"""

import os
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI

# 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

user_state = {
    "service": None, "movement": None,
    "time_limit": None, "radius": None,
    "rent": None, "deposit": None, "maint": None
}

chat_history = [
    {"role": "system", "content": "당신은 친절한 부동산 챗봇입니다. 사용자 조건에 맞는 매물을 추천하고 결과를 요약해주세요."}
]

# 🔍 1. 거주지 기준 필터

def search_by_location():
    result = index.query(vector=[0.0] * 1536, top_k=500, include_metadata=True)
    matches = result.matches
    if user_state["service"] == "1":
        key = "walk_time" if user_state["movement"] == "1" else "transit_time"
        matches = [m for m in matches if m.metadata.get(key, 9999) <= user_state["time_limit"]]
    elif user_state["service"] == "2":
        print("(반경 기반 검색은 위경도 거리 계산 필요, 생략 중)")
    return [m for m in matches if m.metadata.get("station") != "미확인역"][:5]

# 💰 2. 예산 기준 필터

def search_by_budget():
    result = index.query(vector=[0.0] * 1536, top_k=500, include_metadata=True)
    matches = result.matches
    return [
        m for m in matches
        if m.metadata.get("rent", 9999) <= user_state["rent"]
        and m.metadata.get("deposit", 99999) <= user_state["deposit"]
        and m.metadata.get("maint", 9999) <= user_state["maint"]
        and m.metadata.get("station") != "미확인역"
    ][:5]

# 🧠 3. GPT 요약 생성

def summarize_results(loc_matches, bud_matches):
    def fmt(items):
        out = ""
        for i, m in enumerate(items, 1):
            md = m.metadata
            out += (f"{i}. {md['address']} ({md['station']}, {md['subway_time']})\n"
                    f"   - 월세 {md['rent']}만 / 보증금 {md['deposit']}만 / 관리비 {md['maint']}만\n")
        return out or "없음"

    prompt = (
        f"[거주지 기준 매물]\n{fmt(loc_matches)}\n\n"
        f"[예산 기준 매물]\n{fmt(bud_matches)}\n\n"
        f"위 정보를 사용자에게 친절하고 자연스럽게 요약해서 안내해줘. 예: 어떤 역 주변에 괜찮은 매물이 있고 어떤 조건에 부합하는지도 알려줘."
    )
    res = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=chat_history + [{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return res.choices[0].message.content.strip()

# 🎬 챗봇 흐름

first_q = "안녕하세요! 부동산 매물 추천을 도와드릴게요.\n1️⃣ 어떤 기준으로 추천할까요?\n1. 소요시간 기준\n2. 반경 기준 (m 단위)"
print(f"\n🤖 챗봇: {first_q}")
chat_history.append({"role": "assistant", "content": first_q})

while True:
    user_input = input("\n🙋 사용자: ").strip()
    if user_input.lower() in ["종료", "exit", "그만"]:
        print("\n👋 대화를 종료합니다.")
        break
    chat_history.append({"role": "user", "content": user_input})

    followup = ""
    if user_state["service"] is None and user_input in ["1", "2"]:
        user_state["service"] = user_input
        followup = "2️⃣ 이동 방법은?\n1. 도보\n2. 대중교통\n3. 상관없음" if user_input == "1" else "반경(m)을 입력해주세요."

    elif user_state["service"] == "1" and user_state["movement"] is None and user_input in ["1", "2", "3"]:
        user_state["movement"] = user_input
        followup = "몇 분까지 괜찮으신가요? (예: 10)"

    elif user_state["service"] == "1" and user_state["time_limit"] is None and user_input.isdigit():
        user_state["time_limit"] = int(user_input)
        followup = "월세 예산은 얼마까지 괜찮으신가요? (만원 단위)"

    elif user_state["service"] == "2" and user_state["radius"] is None and user_input.isdigit():
        user_state["radius"] = int(user_input)
        followup = "월세 예산은 얼마까지 괜찮으신가요? (만원 단위)"

    elif user_state["rent"] is None and user_input.isdigit():
        user_state["rent"] = int(user_input)
        followup = "보증금은 얼마까지 괜찮으신가요?"

    elif user_state["deposit"] is None and user_input.isdigit():
        user_state["deposit"] = int(user_input)
        followup = "관리비는 얼마까지 괜찮으신가요?"

    elif user_state["maint"] is None and user_input.isdigit():
        user_state["maint"] = int(user_input)
        followup = "감사합니다! 조건에 맞는 매물을 찾고 있어요..."
    else:
        followup = "숫자 또는 번호로 다시 입력해주실 수 있을까요?"

    chat_history.append({"role": "assistant", "content": followup})
    print(f"\n🤖 챗봇: {followup}")

    # 모든 조건 충족 시 결과 요약 출력
    ready = all([user_state["rent"], user_state["deposit"], user_state["maint"]]) and (
        (user_state["service"] == "1" and user_state["movement"] and user_state["time_limit"])
        or (user_state["service"] == "2" and user_state["radius"])
    )
    if ready:
        loc_matches = search_by_location()
        bud_matches = search_by_budget()
        summary = summarize_results(loc_matches, bud_matches)
        print(f"\n🤖 챗봇 요약:\n{summary}")
        break