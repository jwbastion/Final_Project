
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from query_engine import run_query_mode

dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
print("[DEBUG] .env 실제 경로:", dotenv_path)

# ✅ 덮어쓰기 명시
load_dotenv(dotenv_path=dotenv_path, override=True)

print("[DEBUG] QueryTest3에서 불러온 HOST =", os.getenv("POSTGRES_HOST"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_question(prompt):
    return input(prompt + "\n> ").strip()

def parse_with_llm(user_message, system_prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    content = response.choices[0].message.content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        raise ValueError(f"LLM 응답을 JSON으로 파싱할 수 없습니다:\n{content}")

def run_cli_chatbot():
    user_conditions = {}

    msg = ask_question("월세, 보증금, 관리비는 각각 얼마까지 괜찮으신가요?")
    parsed = parse_with_llm(msg, "사용자의 예산 조건(월세, 보증금, 관리비)을 다음의 영어 키로 JSON 딕셔너리 형태로 반환해줘: rent, deposit, maint. 값은 반드시 정수형으로. 예: {\"rent\": 50, \"deposit\": 500, \"maint\": 10}")

    user_conditions.update(parsed)

    msg = ask_question("지하철까지는 도보, 대중교통 중 어떤 이동을 선호하시나요? 그리고 최대 몇 분까지 괜찮으세요?")
    parsed = parse_with_llm(msg, "이동 방식(walk 또는 transit)과 시간 제한을 파싱해서 movement, time_limit 형태로 JSON 딕셔너리로 줘.")
    user_conditions.update(parsed)

    msg = ask_question("집 주변에 어떤 시설이 있으면 좋겠다고 생각하시나요? (예: 공원, 카페, 병원 등)")
    parsed = parse_with_llm(
        msg,
        "사용자가 선호하는 시설을 infra_park, infra_cafe 등 내부 키로 변환해서 JSON 딕셔너리 형태로 반환해줘. 예: {\"selected_infras\": [\"infra_park\", \"infra_cafe\"]}"
    )
    user_conditions.update(parsed)

    print("\n최종 조건 요약:")
    for k, v in user_conditions.items():
        print(f"{k}: {v}")

    user_lat = 37.5055712636346
    user_lng = 126.941856308051

    results = run_query_mode(user_lat, user_lng, user_conditions)

    print("\n추천 매물 결과:")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['address']} | 월세 {r['rent']}만 | 보증금 {r['deposit']}만 | 인프라점수: {r['infra_score']:.2f}")

if __name__ == "__main__":
    run_cli_chatbot()