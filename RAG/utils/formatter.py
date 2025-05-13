from models.infra_types import INFRA_TYPES

def print_summary(user_state, user_infra_preferences=None):
    """현재까지의 설정 요약을 출력하는 함수"""
    print(f"\n## 현재까지의 설정 요약")
    
    # 예산 정보
    if user_state.get('rent'):
        print(f"- 월세: {user_state.get('rent')}만원")
    if user_state.get('deposit'):
        print(f"- 보증금: {user_state.get('deposit')}만원")
    if user_state.get('maint'):
        print(f"- 관리비: {user_state.get('maint')}만원")
    
    # 위치 기준 정보
    if user_state.get('service'):
        print(f"- 추천 기준: {user_state.get('service')}")
    if user_state.get('radius'):
        print(f"- 반경: {user_state.get('radius')}m")
    if user_state.get('time_limit'):
        print(f"- 소요시간: {user_state.get('time_limit')}분")
    if user_state.get('movement') and user_state.get('movement') != "상관없음":
        print(f"- 이동방법: {user_state.get('movement')}")
    
    # 인프라 정보
    if user_infra_preferences:
        infra_names = [next((x["name"] for x in INFRA_TYPES if x["code"] == i), i) for i in user_infra_preferences.keys()]
        print(f"- 선택한 인프라: {', '.join(infra_names)}")
    
    # 인프라 세부 정보
    if 'infra_details' in user_state.state:
        for infra_type, details in user_state.state['infra_details'].items():
            infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type)
            for q_idx, answer in details.items():
                print(f"  - {infra_name} 세부 설정 {q_idx+1}: {answer}")
    
    # 매물 특성 정보
    if 'property_features' in user_state.state:
        from models.infra_types import PROPERTY_FEATURE_QUESTIONS
        for feature_code, value in user_state.state['property_features'].items():
            feature_name = next((q["question"].split("?")[0] for q in PROPERTY_FEATURE_QUESTIONS if q["code"] == feature_code), feature_code)
            print(f"- {feature_name}: {value}")

def format_time_info(prop, movement):
    """이동 시간 정보 포맷팅"""
    walk = prop.get("walk_time", 9999)
    trans = prop.get("transit_time", 9999)
    
    if movement == "도보": 
        return f"도보 {walk}분"
    elif movement == "대중교통": 
        return f"대중교통 {trans}분"
    else:
        t, mode = (walk, "도보") if walk <= trans else (trans, "대중교통")
        return f"{mode} {t}분"