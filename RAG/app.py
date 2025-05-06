from chatbot import RealEstateChatbot
from config import INFRA_TYPES

def main():
    print("🏠 부동산 매물 추천 챗봇을 시작합니다.")
    print("원하시는 조건을 알려주시면 최적의 매물을 추천해드립니다.")
    
    chatbot = RealEstateChatbot()
    
    budget_names = {'rent': '월세', 'deposit': '보증금', 'maint': '관리비'}
    current_key = 'rent'
    cur = chatbot.user_state.get(current_key)
    
    print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
    
    setup_stage = "budget"
    
    user_infra_preferences = {}
    
    while True:
        user_input = input("\n🙋 사용자: ")
        if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
            print("챗봇을 종료합니다. 감사합니다!")
            break
        
        if setup_stage == "budget":
            if current_key == 'rent':
                if user_input.lower() not in ["없음", "기본"]:
                    num = ''.join(filter(str.isdigit, user_input))
                    if num:
                        chatbot.user_state.update(current_key, int(num))
                current_key = 'deposit'
                cur = chatbot.user_state.get(current_key)
                print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
            
            elif current_key == 'deposit':
                if user_input.lower() not in ["없음", "기본"]:
                    num = ''.join(filter(str.isdigit, user_input))
                    if num:
                        chatbot.user_state.update(current_key, int(num))
                current_key = 'maint'
                cur = chatbot.user_state.get(current_key)
                print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
            
            elif current_key == 'maint':
                if user_input.lower() not in ["없음", "기본"]:
                    num = ''.join(filter(str.isdigit, user_input))
                    if num:
                        chatbot.user_state.update(current_key, int(num))
                
                rent = chatbot.user_state.get("rent")
                deposit = chatbot.user_state.get("deposit")
                maint = chatbot.user_state.get("maint")
                
                summary = f"""
📌 설정된 예산 정보:
- 월세: {rent}만원
- 보증금: {deposit}만원
- 관리비: {maint}만원

어떤 기준으로 추천할까요?
1. 소요시간 기준
2. 반경 기준 (m 단위)
3. 상관없음
"""
                print(f"\n🤖 챗봇: {summary}")
                current_key = 'service'
                setup_stage = "location"
        
        elif setup_stage == "location":
            if current_key == 'service':
                service_map = {
                    "1": "소요시간", "소요시간": "소요시간", 
                    "2": "반경", "반경": "반경",
                    "3": "상관없음", "상관없음": "상관없음"
                }
                
                service = service_map.get(user_input.lower(), "소요시간")
                chatbot.user_state.update("service", service)
                
                if service == "소요시간":
                    print("\n🤖 챗봇: 이동 방법? 1.도보 2.대중교통 3.상관없음")
                    current_key = 'movement'
                
                elif service == "반경":
                    print("\n🤖 챗봇: 반경(m)을 입력하세요")
                    current_key = 'radius'
                
                else:
                    chatbot.user_state.update("movement", "상관없음")
                    setup_stage = "infra"
                    print("\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.")
                    for i, infra in enumerate(INFRA_TYPES, 1):
                        print(f"{i}. {infra['name']} - {infra['description']}")
                    print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")
            
            elif current_key == 'movement':
                movement_map = {
                    "1": "도보", "도보": "도보",
                    "2": "대중교통", "대중교통": "대중교통",
                    "3": "상관없음", "상관없음": "상관없음"
                }
                
                movement = movement_map.get(user_input.lower(), "대중교통")
                chatbot.user_state.update("movement", movement)
                
                print("\n🤖 챗봇: 최대 소요시간(분)?")
                current_key = 'time_limit'
            
            elif current_key == 'time_limit':
                try:
                    time_limit = int(''.join(filter(str.isdigit, user_input)))
                    chatbot.user_state.update("time_limit", time_limit)
                except:
                    chatbot.user_state.update("time_limit", 15)
                
                setup_stage = "infra"
                print("\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.")
                for i, infra in enumerate(INFRA_TYPES, 1):
                    print(f"{i}. {infra['name']} - {infra['description']}")
                print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")
            
            elif current_key == 'radius':
                try:
                    radius = int(''.join(filter(str.isdigit, user_input)))
                    chatbot.user_state.update("radius", radius)
                except:
                    chatbot.user_state.update("radius", 500)
                
                setup_stage = "infra"
                print("\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.")
                for i, infra in enumerate(INFRA_TYPES, 1):
                    print(f"{i}. {infra['name']} - {infra['description']}")
                print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")
        
        elif setup_stage == "infra":
            try:
                if ',' in user_input:
                    selections = [int(s.strip()) for s in user_input.split(',')]
                else:
                    selections = [int(s.strip()) for s in user_input.split()]
                
                if not selections or len(selections) > 3 or not all(1 <= s <= len(INFRA_TYPES) for s in selections):
                    print(f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)")
                    continue
                
                weights = [5, 3, 1]
                for i, selection in enumerate(selections):
                    if i < len(weights):
                        infra_type = INFRA_TYPES[selection-1]["code"]
                        user_infra_preferences[infra_type] = weights[i]
                
                print(f"선택한 인프라: {user_infra_preferences}")
                
                setup_stage = "complete"
                chatbot.user_state.update("infra_preferences", user_infra_preferences)
                chatbot.setup_complete = True
                
                try:
                    recommendations = chatbot.recommender.get_recommendations()
                    
                    result = "설정이 완료되었습니다. 다음은 추천 매물입니다:\n\n"
                    
                    if not recommendations["location_based"] and not recommendations["budget_based"] and not recommendations["combined"]:
                        result += "설정하신 조건에 맞는 매물을 찾지 못했습니다. 다음과 같이 조건을 변경해보세요:\n\n"
                        result += "1. 예산 범위를 넓혀보세요 (월세, 보증금 상향 조정)\n"
                        result += "2. 검색 반경을 넓혀보세요 (현재 반경 → 더 넓은 범위)\n"
                        result += "3. 다른 지역도 고려해보세요\n\n"
                        result += "조건을 변경하시겠어요? 어떤 조건을 변경하고 싶으신가요?"
                    else:
                        if recommendations["location_based"]:
                            result += "**위치 기반 추천 매물**\n"
                            for i, prop in enumerate(recommendations["location_based"], 1):
                                infra_score = prop.get("infra_score", 0)
                                result += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                                
                                if prop.get("infra_details"):
                                    result += "   인프라 세부 정보:\n"
                                    for infra_type, detail in prop["infra_details"].items():
                                        if detail.get("score", 0) > 0:
                                            infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type)
                                            result += f"   - {infra_name}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
                        
                        if recommendations["budget_based"]:
                            result += "\n**예산 기반 추천 매물**\n"
                            for i, prop in enumerate(recommendations["budget_based"], 1):
                                infra_score = prop.get("infra_score", 0)
                                result += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                                
                                if prop.get("infra_details"):
                                    result += "   인프라 세부 정보:\n"
                                    for infra_type, detail in prop["infra_details"].items():
                                        if detail.get("score", 0) > 0:
                                            infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type)
                                            result += f"   - {infra_name}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
                        
                        if recommendations["combined"]:
                            result += "\n**종합 추천 매물 (위치+예산+인프라)**\n"
                            for i, prop in enumerate(recommendations["combined"], 1):
                                infra_score = prop.get("infra_score", 0)
                                result += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                                
                                if prop.get("infra_details"):
                                    result += "   인프라 세부 정보:\n"
                                    for infra_type, detail in prop["infra_details"].items():
                                        if detail.get("score", 0) > 0:
                                            infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type)
                                            result += f"   - {infra_name}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
                        
                        result += "\n이 중에서 어떤 매물이 마음에 드시나요? 또는 다른 조건으로 검색하고 싶으신가요?"
                    
                    print(f"\n🤖 챗봇: {result}")
                
                except Exception as e:
                    print(f"\n🤖 챗봇: 추천 매물을 가져오는 중 오류가 발생했습니다: {e}")
                    print("\n🤖 챗봇: 죄송합니다. 매물 검색 중 문제가 발생했습니다. 다시 시도해주시거나 다른 조건으로 검색해보세요.")
            
            except ValueError:
                print(f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)")
        
        elif setup_stage == "complete":
            response = chatbot.process_message(user_input)
            print(f"\n🤖 챗봇: {response}")

if __name__ == "__main__":
    main()
