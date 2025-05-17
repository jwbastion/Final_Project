import time
from openai import OpenAI
from pinecone import Pinecone
from RAG.api.config import OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME
from RAG.api.models import UserState
from RAG.api.recommender import RealEstateRecommender
import sys
import io
import traceback

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding="utf-8")

# 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)


class LLMProcessor:
    def __init__(self, client):
        self.client = client

    def generate_response(self, user_message, context, chat_history):
        """LLM을 사용하여 응답 생성"""
        # 대화 이력 포맷팅
        history_text = ""
        for entry in chat_history:
            history_text += f"사용자: {entry['user']}\n봇: {entry['bot']}\n\n"

        # 컨텍스트 포맷팅
        context_text = self._format_context(context)

        # LLM 프롬프트 구성
        prompt = f"""당신은 부동산 매물 추천 AI 챗봇입니다. 사용자의 위치, 예산, 이동 방식, 인프라 선호도, 매물 특성 등을 고려하여 최적의 매물을 추천해주세요.

대화 이력:
{history_text}

추천 매물 정보:
{context_text}

사용자 메시지: {user_message}

친절하고 도움이 되는 응답을 제공해주세요. 사용자가 특정 매물에 관심을 보이면 더 자세한 정보를 제공하고, 
추가 질문이 있으면 답변해주세요. 매물이 없는 경우에는 검색 조건을 변경해보라고 제안해주세요.
"""

        try:
            # LLM 호출
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7,
                max_tokens=1000,
            )

            return response.choices[0].message.content
        except Exception:

            print("LLM 응답 생성 오류:\n", traceback.format_exc())
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다. 다시 시도해주세요."

    def _format_context(self, context):
        """컨텍스트 포맷팅"""
        context_text = ""

        # 각 타입별 추천 매물 정보 포맷팅
        for rec_type in ["location_based", "budget_based", "combined"]:
            if not context.get(rec_type):
                continue

            type_name = {
                "location_based": "위치 기반",
                "budget_based": "예산 기반",
                "combined": "종합",
            }.get(rec_type)

            context_text += f"\n{type_name} 추천 매물:\n"
            for i, prop in enumerate(context[rec_type], 1):
                infra_score = prop.get("infra_score", 0)
                context_text += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                context_text += f"   층수: {prop['floor']}, 난방: {prop['heating_type']}, 주차: {'가능' if prop['parking'] else '불가능'}\n"
                context_text += f"   시설: {prop.get('facilities', '')}, 조망: {prop.get('view', '')}\n"

                # 인프라 세부 정보 추가
                if prop.get("infra_details"):
                    context_text += "  인프라 세부 정보:\n"
                    for infra_type, detail in prop["infra_details"].items():
                        if detail.get("score", 0) > 0:
                            context_text += f"    - {infra_type}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"

        # 추천 매물이 없는 경우
        if not context_text:
            context_text = "현재 설정하신 조건에 맞는 매물을 찾지 못했습니다. 다음과 같이 조건을 변경해보세요:\n"
            context_text += "1. 예산 범위를 넓혀보세요 (월세, 보증금 상향 조정)\n"
            context_text += "2. 검색 반경을 넓혀보세요 (현재 반경 → 더 넓은 범위)\n"
            context_text += "3. 다른 지역도 고려해보세요\n"

        return context_text


class RealEstateChatbot:
    def __init__(self, user_uuid=None):
        self.user_state = UserState(user_uuid)
        self.recommender = RealEstateRecommender(index, self.user_state)
        self.llm = LLMProcessor(client)
        self.setup_complete = False

    def process_message(self, user_message: str):
        def extract_number(text):
            num = "".join(filter(str.isdigit, text))
            return int(num) if num else None

        # 상태 초기화
        if not self.user_state.get("setup_stage"):
            self.user_state.update("setup_stage", "budget")
            self.user_state.update("current_key", "rent")
            return "안녕하세요! 👋 저는 부동산 추천 챗봇입니다.\n먼저, 월세 예산은 얼마까지 가능하신가요? (숫자만 입력해주세요)"

        setup_stage = self.user_state.get("setup_stage")
        current_key = self.user_state.get("current_key")

        # 1️⃣ 예산 설정 단계
        if setup_stage == "budget":
            if current_key in ["rent", "deposit", "maint"]:
                if user_message.lower() not in ["없음", "기본"]:
                    num = extract_number(user_message)
                    if num is not None:
                        self.user_state.update(current_key, num)
                        return_msg = f"{num}만원으로 설정했습니다."
                    else:
                        return f"{current_key} 값을 숫자로 입력해주세요."

                # 다음 key 설정
                key_order = ["rent", "deposit", "maint"]
                next_index = key_order.index(current_key) + 1
                if next_index < len(key_order):
                    next_key = key_order[next_index]
                    self.user_state.update("current_key", next_key)
                    cur = self.user_state.get(next_key)
                    return f"{return_msg}\n현재 설정된 {next_key}은 {cur}만원입니다. 변경하고 싶다면 입력해주세요."
                else:
                    self.user_state.update("setup_stage", "location")
                    self.user_state.update("current_key", "service")
                    return (
                        "예산 설정이 완료되었습니다.\n"
                        "어떤 기준으로 추천할까요?\n1. 소요시간\n2. 반경\n3. 상관없음"
                    )

        # 2️⃣ 위치 기준 설정
        if setup_stage == "location":
            if current_key == "service":
                ui = user_message.strip().lower()
                if "소요" in ui or ui == "1":
                    service = "소요시간"
                elif "반경" in ui or ui == "2":
                    service = "반경"
                elif "상관" in ui or ui == "3":
                    service = "상관없음"
                else:
                    return "1. 소요시간 / 2. 반경 / 3. 상관없음 중에서 선택해주세요."

                self.user_state.update("service", service)

                # 다음 흐름 설정
                if service == "소요시간":
                    self.user_state.update("current_key", "movement")
                    return (
                        "이동 방법은 무엇인가요? (1. 도보 / 2. 대중교통 / 3. 상관없음)"
                    )
                elif service == "반경":
                    self.user_state.update("current_key", "radius")
                    return "반경(m)을 입력해주세요 (예: 500)"
                else:
                    self.user_state.update("movement", "상관없음")
                    self.user_state.update("setup_stage", "infra")
                    return self._infra_intro()

            if current_key == "movement":
                move_map = {"1": "도보", "2": "대중교통", "3": "상관없음"}
                move = move_map.get(user_message.strip(), "도보")
                self.user_state.update("movement", move)
                self.user_state.update("current_key", "time_limit")
                return "최대 몇 분 이내를 원하시나요? (예: 20)"

            if current_key == "time_limit":
                num = extract_number(user_message)
                if num:
                    self.user_state.update("time_limit", num)
                    self.user_state.update("setup_stage", "infra")
                    return self._infra_intro()
                else:
                    return "숫자로 입력해주세요. (예: 20)"

            if current_key == "radius":
                num = extract_number(user_message)
                if num:
                    self.user_state.update("radius", num)
                    self.user_state.update("setup_stage", "infra")
                    return self._infra_intro()
                else:
                    return "숫자로 입력해주세요. (예: 500)"

        # 3️⃣ 인프라 선택
        if setup_stage == "infra":
            if not self.user_state.get("infra_preferences"):
                try:
                    selections = [
                        int(s.strip()) for s in user_message.replace(",", " ").split()
                    ]
                    if not (1 <= len(selections) <= 3):
                        raise ValueError
                    from RAG.api.config import INFRA_TYPES

                    weights = [5, 3, 1]
                    prefs = {}
                    for i, s in enumerate(selections):
                        code = INFRA_TYPES[s - 1]["code"]
                        prefs[code] = weights[i]
                    self.user_state.update("infra_preferences", prefs)
                    self.user_state.update("setup_stage", "features")
                    self.user_state.update("feature_index", 0)
                    from RAG.api.config import PROPERTY_FEATURE_QUESTIONS

                    return PROPERTY_FEATURE_QUESTIONS[0]["question"]
                except:
                    return "최대 3개까지 숫자로 정확히 선택해주세요. (예: 1 3 5)"

        # 4️⃣ 매물 특성
        if setup_stage == "features":
            from RAG.api.config import PROPERTY_FEATURE_QUESTIONS

            idx = self.user_state.get("feature_index", 0)
            if idx < len(PROPERTY_FEATURE_QUESTIONS):
                code = PROPERTY_FEATURE_QUESTIONS[idx]["code"]
                self.user_state.update(f"feature_{code}", user_message.strip())
                idx += 1
                self.user_state.update("feature_index", idx)
                if idx < len(PROPERTY_FEATURE_QUESTIONS):
                    return PROPERTY_FEATURE_QUESTIONS[idx]["question"]
                else:
                    self.user_state.update("setup_stage", "complete")

        # 5️⃣ 추천 및 응답
        if self.user_state.get("setup_stage") == "complete":
            try:
                recommendations = self.recommender.get_recommendations()
            except Exception as e:
                print(f"추천 오류: {e}")
                recommendations = {
                    "location_based": [],
                    "budget_based": [],
                    "combined": [],
                }

            chat_history = self.user_state.get_history()
            response = self.llm.generate_response(
                user_message, recommendations, chat_history
            )
            self.user_state.add_to_history(user_message, response)
            return response

        return "질문을 인식하지 못했습니다. 다시 입력해주세요."

    def _infra_intro(self):
        from RAG.api.config import INFRA_TYPES

        message = (
            "\n🤖 챗봇: 다음 중 중요하게 생각하는 인프라를 최대 3개까지 선택해주세요:\n"
        )
        for i, infra in enumerate(INFRA_TYPES, 1):
            message += f"{i}. {infra['name']} - {infra['description']}\n"
        return message + "\n번호를 입력해주세요 (예: 1 3 5)"


def setup_infrastructure_v2(chatbot):
    """개선된 인프라 선호도 설정 함수"""
    from RAG.api.config import INFRA_TYPES, INFRA_DETAIL_QUESTIONS_V2
    from RAG.api.utils import print_summary

    print(
        "\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요."
    )

    # 1단계: 중요 인프라 선택 (기존 로직 유지)
    for i, infra in enumerate(INFRA_TYPES, 1):
        print(f"{i}. {infra['name']} - {infra['description']}")
    print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")

    user_input = input("\n🙋 사용자: ")

    if user_input.lower() in ["종료", "끝", "exit", "quit"]:
        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
        exit(0)

    user_infra_preferences = {}
    try:
        # 쉼표나 공백으로 구분된 입력 처리
        if "," in user_input:
            selections = [int(s.strip()) for s in user_input.split(",")]
        else:
            selections = [int(s.strip()) for s in user_input.split()]

        # 선택 검증
        if (
            not selections
            or len(selections) > 3
            or not all(1 <= s <= len(INFRA_TYPES) for s in selections)
        ):
            print(
                f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요."
            )
            return setup_infrastructure_v2(chatbot)

        # 선택한 인프라 저장 (가중치: 1순위=5, 2순위=3, 3순위=1)
        weights = [5, 3, 1]
        selected_infra_types = []
        for i, selection in enumerate(selections):
            if i < len(weights):  # 최대 3개까지만 처리
                infra_type = INFRA_TYPES[selection - 1]["code"]
                user_infra_preferences[infra_type] = weights[i]
                selected_infra_types.append(infra_type)

        # 사용자 입력 처리 후 응답 및 요약
        print(f"\n🤖 챗봇: 선택한 인프라를 저장했습니다.")
        chatbot.user_state.update("infra_preferences", user_infra_preferences)
        print_summary(chatbot, user_infra_preferences)

        # 인프라 세부 정보 초기화
        infra_details = {}

        # 2단계: 선택된 인프라에 대해 공통 질문 및 세부 질문
        for infra_type in selected_infra_types:
            infra_name = next(
                (x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type
            )
            print(f"\n🤖 챗봇: {infra_name}에 대한 질문입니다.")

            # 인프라별 세부 정보 저장소 초기화
            infra_details[infra_type] = {}

            # 공통 질문 처리
            importance = ask_question(
                f"이 시설이 얼마나 중요한가요? (1: 별로 중요하지 않음 ~ 5: 매우 중요함)"
            )
            infra_details[infra_type]["common_importance"] = importance

            distance = ask_question(
                f"이 시설까지 도보 몇 분 이내가 좋으신가요? (숫자만 입력해주세요)"
            )
            infra_details[infra_type]["common_distance"] = distance

            frequency = ask_question(
                f"이 시설을 얼마나 자주 이용하실 계획인가요? (1: 거의 이용 안함 ~ 5: 거의 매일)"
            )
            infra_details[infra_type]["common_frequency"] = frequency

            # 중요도가 높은 경우(4-5점)에만 세부 질문
            if (
                importance in ["4", "5"]
                and infra_type in INFRA_DETAIL_QUESTIONS_V2["specific_questions"]
            ):
                print(
                    f"\n🤖 챗봇: {infra_name}이 중요하시군요! 조금 더 자세히 알려주세요."
                )

                # 인프라별 고유 질문
                specific_questions = INFRA_DETAIL_QUESTIONS_V2[
                    "specific_questions"
                ].get(infra_type, {})
                for q_code, question in specific_questions.items():
                    answer = ask_question(question)
                    infra_details[infra_type][f"specific_{q_code}"] = answer

        # 인프라 세부 정보 저장
        chatbot.user_state.update("infra_details", infra_details)

        return user_infra_preferences

    except ValueError:
        print(
            f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요."
        )
        return setup_infrastructure_v2(chatbot)


def ask_question(question):
    """질문 표시하고 응답 처리하는 헬퍼 함수"""
    print(question)
    answer = input("\n🙋 사용자: ")
    if answer.lower() in ["종료", "끝", "exit", "quit"]:
        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
        exit(0)
    return answer
