from models import UserState
from recommender import RealEstateRecommender
from llm_processor import LLMProcessor
from config import index, client, db_config, INFRA_TYPES

class RealEstateChatbot:
    def __init__(self):
        self.user_state = UserState()
        self.recommender = RealEstateRecommender(index, self.user_state, db_config)
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
        response = self.llm.generate_response(user_message, recommendations, chat_history)
        
        # 대화 이력 저장
        self.user_state.add_to_history(user_message, response)
        
        return response
