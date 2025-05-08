import math
from config import infra_types

def haversine(lat1, lng1, lat2, lng2):
    """두 지점 간의 거리 계산 (미터 단위)"""
    R = 6371000  # 지구 반경 (미터)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def print_summary(chatbot, user_infra_preferences=None):
    """현재까지의 설정 요약을 출력하는 함수"""
    print(f"\n## 현재까지의 설정 요약")
    
    # 예산 정보
    if chatbot.user_state.get('rent'):
        print(f"- 월세: {chatbot.user_state.get('rent')}만원")
    if chatbot.user_state.get('deposit'):
        print(f"- 보증금: {chatbot.user_state.get('deposit')}만원")
    if chatbot.user_state.get('maint'):
        print(f"- 관리비: {chatbot.user_state.get('maint')}만원")
    
    # 위치 기준 정보
    if chatbot.user_state.get('service'):
        print(f"- 추천 기준: {chatbot.user_state.get('service')}")
    if chatbot.user_state.get('radius'):
        print(f"- 반경: {chatbot.user_state.get('radius')}m")
    if chatbot.user_state.get('time_limit'):
        print(f"- 소요시간: {chatbot.user_state.get('time_limit')}분")
    if chatbot.user_state.get('movement') and chatbot.user_state.get('movement') != "상관없음":
        print(f"- 이동방법: {chatbot.user_state.get('movement')}")
    
    # 인프라 정보
    if user_infra_preferences:
        infra_names = [next((x["name"] for x in infra_types if x["code"] == i), i) for i in user_infra_preferences.keys()]
        print(f"- 선택한 인프라: {', '.join(infra_names)}")
    
    # 인프라 세부 정보
    if hasattr(chatbot.user_state, 'state') and 'infra_details' in chatbot.user_state.state:
        for infra_type, details in chatbot.user_state.state['infra_details'].items():
            infra_name = next((x["name"] for x in infra_types if x["code"] == infra_type), infra_type)
            for q_idx, answer in details.items():
                print(f"  - {infra_name} 세부 설정 {q_idx+1}: {answer}")
    
    # 매물 특성 정보
    if hasattr(chatbot.user_state, 'state') and 'property_features' in chatbot.user_state.state:
        for feature_code, value in chatbot.user_state.state['property_features'].items():
            feature_name = next((q["question"].split("?")[0] for q in property_feature_questions if q["code"] == feature_code), feature_code)
            print(f"- {feature_name}: {value}")
