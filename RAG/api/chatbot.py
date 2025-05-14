import time
from openai import OpenAI
from pinecone import Pinecone
from RAG.api.config import OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME
from RAG.api.models import UserState
from RAG.api.recommender import RealEstateRecommender

# OpenAI 및 Pinecone 클라이언트 초기화
client = OpenAI(api_key=OPENAI_API_KEY)
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)


class LLMProcessor:
    def __init__(self, client):
        self.client = client

    def generate_response(self, user_message, context, chat_history):
        """LLM을 사용하여 응답 생성"""
        # 대화 이력 및 컨텍스트 포맷팅
        history_text = ""
        for entry in chat_history:
            history_text += f"사용자: {entry['user']}\n봇: {entry['bot']}\n\n"

        # 컨텍스트 포맷팅
        context_text = ""
        if context.get("location_based"):
            context_text += "위치 기반 추천 매물:\n"
            for i, prop in enumerate(context["location_based"], 1):
                infra_score = prop.get("infra_score", 0)
                context_text += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                context_text += f"   층수: {prop['floor']}, 난방: {prop['heating_type']}, 주차: {'가능' if prop['parking'] else '불가능'}\n"
                context_text += f"   시설: {prop['facilities']}, 조망: {prop['view']}\n"

                # 인프라 세부 정보 추가
                if prop.get("infra_details"):
                    context_text += "  인프라 세부 정보:\n"
                    for infra_type, detail in prop["infra_details"].items():
                        if detail.get("score", 0) > 0:
                            context_text += f"    - {infra_type}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"

        if context.get("budget_based"):
            context_text += "\n예산 기반 추천 매물:\n"
            for i, prop in enumerate(context["budget_based"], 1):
                infra_score = prop.get("infra_score", 0)
                context_text += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                context_text += f"   층수: {prop['floor']}, 난방: {prop['heating_type']}, 주차: {'가능' if prop['parking'] else '불가능'}\n"
                context_text += f"   시설: {prop['facilities']}, 조망: {prop['view']}\n"

                # 인프라 세부 정보 추가
                if prop.get("infra_details"):
                    context_text += "  인프라 세부 정보:\n"
                    for infra_type, detail in prop["infra_details"].items():
                        if detail.get("score", 0) > 0:
                            context_text += f"    - {infra_type}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"

        if context.get("combined"):
            context_text += "\n종합 추천 매물 (위치+예산+인프라):\n"
            for i, prop in enumerate(context["combined"], 1):
                infra_score = prop.get("infra_score", 0)
                context_text += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                context_text += f"   층수: {prop['floor']}, 난방: {prop['heating_type']}, 주차: {'가능' if prop['parking'] else '불가능'}\n"
                context_text += f"   시설: {prop['facilities']}, 조망: {prop['view']}\n"

                # 인프라 세부 정보 추가
                if prop.get("infra_details"):
                    context_text += "  인프라 세부 정보:\n"
                    for infra_type, detail in prop["infra_details"].items():
                        if detail.get("score", 0) > 0:
                            context_text += f"    - {infra_type}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"

        # 추천 매물이 없는 경우
        if (
            not context.get("location_based")
            and not context.get("budget_based")
            and not context.get("combined")
        ):
            context_text = "현재 설정하신 조건에 맞는 매물을 찾지 못했습니다. 다음과 같이 조건을 변경해보세요:\n"
            context_text += "1. 예산 범위를 넓혀보세요 (월세, 보증금 상향 조정)\n"
            context_text += "2. 검색 반경을 넓혀보세요 (현재 반경 → 더 넓은 범위)\n"
            context_text += "3. 다른 지역도 고려해보세요\n"

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
                model="gpt-3.5-turbo",  # 또는 사용 가능한 모델
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7,
                max_tokens=1000,
            )

            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 응답 생성 오류: {e}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다. 다시 시도해주세요."


class RealEstateChatbot:
    def __init__(self, user_uuid=None):
        self.user_state = UserState(user_uuid)
        self.recommender = RealEstateRecommender(index, self.user_state)
        self.llm = LLMProcessor(client)
        self.setup_complete = False

    def process_message(self, user_message):
        """사용자 메시지 처리 (설정 완료 후)"""
        # 추천 결과 가져오기
        try:
            recommendations = self.recommender.get_recommendations()
        except Exception as e:
            print(f"추천 결과 가져오기 오류: {e}")
            recommendations = {"location_based": [], "budget_based": [], "combined": []}

        chat_history = self.user_state.get_history()

        # LLM을 통한 응답 생성
        response = self.llm.generate_response(
            user_message, recommendations, chat_history
        )

        # 대화 이력 저장
        self.user_state.add_to_history(user_message, response)

        return response
