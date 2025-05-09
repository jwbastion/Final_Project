import time

class UserState:
    """사용자 상태 관리 클래스"""
    
    def __init__(self):
        # 초기 설정 (기본값)
        self.state = {
            "lat": 37.5055712636346,
            "lng": 126.941856308051,
            "service": None,
            "movement": None,
            "time_limit": None,
            "radius": None,
            "rent": 50,
            "deposit": 1000,
            "maint": 30,
            "infra_preferences": {},
            "infra_details": {},  # 인프라 세부 정보 저장
            "property_features": {},  # 매물 특성 저장
            "chat_history": []
        }
    
    def update(self, key, value):
        """상태 업데이트"""
        if key.startswith("infra_detail_"):
            parts = key.split("_", 3)  # infra_detail_traffic_subway_0 -> ['infra', 'detail', 'traffic', 'subway_0']
            
            if len(parts) >= 4:
                # 인프라 타입 (traffic_subway)과 질문 인덱스(0) 추출
                infra_type = parts[2] + "_" + parts[3].split("_")[0]  # traffic_subway
                
                try:
                    question_idx = int(parts[3].split("_")[1]) if "_" in parts[3] else 0
                except (ValueError, IndexError):
                    question_idx = 0
                    
                if "infra_details" not in self.state:
                    self.state["infra_details"] = {}
                if infra_type not in self.state["infra_details"]:
                    self.state["infra_details"][infra_type] = {}
                
                self.state["infra_details"][infra_type][question_idx] = value
            else:
                # 형식이 맞지 않으면 그냥 저장
                self.state[key] = value
        elif key.startswith("feature_"):
            feature_code = key.split("_")[1]
            if "property_features" not in self.state:
                self.state["property_features"] = {}
            self.state["property_features"][feature_code] = value
        else:
            self.state[key] = value
    
    def get(self, key, default=None):
        return self.state.get(key, default)
    
    def add_to_history(self, user_message, bot_response):
        self.state["chat_history"].append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": time.time()
        })
    
    def get_history(self, limit=5):
        return self.state["chat_history"][-limit:]