import os
from config import DB_CONFIG, OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME
from models.infra_types import INFRA_TYPES, INFRA_DETAIL_QUESTIONS, PROPERTY_FEATURE_QUESTIONS
from models.user_state import UserState
from services.db_service import InfraDataAccessor
from services.vector_service import VectorService
from services.llm_service import LLMProcessor
from services.recommender import RealEstateRecommender
from utils.formatter import print_summary, format_time_info
from chatbot.chatbot import RealEstateChatbot

def main():
    print("🏠 부동산 매물 추천 챗봇을 시작합니다.")
    print("원하시는 조건을 알려주시면 최적의 매물을 추천해드립니다.")
    
    # 필요한 서비스 초기화
    vector_service = VectorService(PINECONE_API_KEY, PINECONE_INDEX_NAME)
    data_accessor = InfraDataAccessor(DB_CONFIG)
    llm_processor = LLMProcessor(OPENAI_API_KEY)
    
    # 챗봇 초기화
    chatbot = RealEstateChatbot(vector_service, data_accessor, llm_processor)
    
    # 예산 관련 변수
    budget_names = {'rent': '월세', 'deposit': '보증금', 'maint': '관리비'}
    current_key = 'rent'
    cur = chatbot.user_state.get(current_key)
    
    # 첫 질문 출력 (사용자 입력 없이)
    print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
    
    # 대화 상태 변수
    setup_stage = "budget"  # 초기 단계: 예산 설정
    
    # 사용자 인프라 선호도 저장
    user_infra_preferences = {}
    
    while True:
        user_input = input("\n🙋 사용자: ")
        if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
            print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
            break
        
        # 예산 설정 단계
        if setup_stage == "budget":
            if current_key == 'rent':
                if user_input.lower() not in ["없음", "기본"]:
                    num = ''.join(filter(str.isdigit, user_input))
                    if num:
                        chatbot.user_state.update("rent", int(num))
                        # 사용자 입력 처리 후 응답 및 요약
                        print(f"\n🤖 챗봇: {num}만원으로 설정했습니다.")
                        print_summary(chatbot.user_state)
                
                # 다음 질문
                current_key = 'deposit'
                cur = chatbot.user_state.get(current_key)
                print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
                continue
            
            elif current_key == 'deposit':
                if user_input.lower() not in ["없음", "기본"]:
                    num = ''.join(filter(str.isdigit, user_input))
                    if num:
                        chatbot.user_state.update(current_key, int(num))
                        # 사용자 입력 처리 후 응답 및 요약
                        print(f"\n🤖 챗봇: {num}만원으로 설정했습니다.")
                        print_summary(chatbot.user_state)
                
                # 다음 질문
                current_key = 'maint'
                cur = chatbot.user_state.get(current_key)
                print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
                continue
            
            elif current_key == 'maint':
                if user_input.lower() not in ["없음", "기본"]:
                    num = ''.join(filter(str.isdigit, user_input))
                    if num:
                        chatbot.user_state.update(current_key, int(num))
                        # 사용자 입력 처리 후 응답 및 요약
                        print(f"\n🤖 챗봇: {num}만원으로 설정했습니다.")
                        print_summary(chatbot.user_state)
                
                # 예산 설정 완료 후 다음 질문
                print("\n🤖 챗봇: 어떤 기준으로 추천할까요?")
                print("1. 소요시간 기준")
                print("2. 반경 기준 (m 단위)")
                print("3. 상관없음")
                
                current_key = 'service'
                setup_stage = "location"
                continue
        
        # 위치 선호도 설정 단계
        elif setup_stage == "location":
            if current_key == 'service':
                service_map = {
                    "1": "소요시간", "소요시간": "소요시간", 
                    "2": "반경", "반경": "반경",
                    "3": "상관없음", "상관없음": "상관없음"
                }
                
                service = service_map.get(user_input.lower(), "소요시간")
                chatbot.user_state.update("service", service)
                
                # 사용자 입력 처리 후 응답 및 요약
                print(f"\n🤖 챗봇: {service} 기준으로 설정했습니다.")
                print_summary(chatbot.user_state)
                
                if service == "소요시간":
                    print("\n🤖 챗봇: 이동 방법? 1.도보 2.대중교통 3.상관없음")
                    current_key = 'movement'
                
                elif service == "반경":
                    print("\n🤖 챗봇: 반경(m)을 입력하세요")
                    current_key = 'radius'
                
                else:  # 상관없음
                    chatbot.user_state.update("movement", "상관없음")
                    setup_stage = "infra"  # 인프라 선호도 조사로 넘어감
                    print("\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.")
                    for i, infra in enumerate(INFRA_TYPES, 1):
                        print(f"{i}. {infra['name']} - {infra['description']}")
                    print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")
                continue
            
            elif current_key == 'movement':
                movement_map = {
                    "1": "도보", "도보": "도보",
                    "2": "대중교통", "대중교통": "대중교통",
                    "3": "상관없음", "상관없음": "상관없음"
                }
                
                movement = movement_map.get(user_input.lower(), "도보")
                chatbot.user_state.update("movement", movement)
                
                # 사용자 입력 처리 후 응답 및 요약
                print(f"\n🤖 챗봇: {movement}로 설정했습니다.")
                print_summary(chatbot.user_state)
                
                print("\n🤖 챗봇: 최대 몇 분 이내를 원하시나요?")
                current_key = 'time_limit'
                continue
            
            elif current_key == 'time_limit':
                try:
                    time_value = int(''.join(filter(str.isdigit, user_input)))
                    chatbot.user_state.update("time_limit", time_value)
                    
                    # 사용자 입력 처리 후 응답 및 요약
                    print(f"\n🤖 챗봇: {time_value}분 이내로 설정했습니다.")
                    print_summary(chatbot.user_state)
                    
                    # 인프라 선호도 조사로 넘어감
                    setup_stage = "infra"
                    print("\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.")
                    for i, infra in enumerate(INFRA_TYPES, 1):
                        print(f"{i}. {infra['name']} - {infra['description']}")
                    print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")
                except:
                    print("\n🤖 챗봇: 숫자로 입력해주세요.")
                continue
            
            elif current_key == 'radius':
                try:
                    radius = int(''.join(filter(str.isdigit, user_input)))
                    chatbot.user_state.update("radius", radius)
                    
                    # 사용자 입력 처리 후 응답 및 요약
                    print(f"\n🤖 챗봇: 반경을 {radius}m로 설정했습니다.")
                    print_summary(chatbot.user_state)
                    
                    # 인프라 선호도 조사로 넘어감
                    setup_stage = "infra"
                    print("\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.")
                    for i, infra in enumerate(INFRA_TYPES, 1):
                        print(f"{i}. {infra['name']} - {infra['description']}")
                    print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")
                except:
                    print("\n🤖 챗봇: 숫자로 입력해주세요.")
                continue
        
        # 인프라 선호도 설정 단계
        elif setup_stage == "infra":
            try:
                # 쉼표나 공백으로 구분된 입력 처리
                if ',' in user_input:
                    selections = [int(s.strip()) for s in user_input.split(',')]
                else:
                    selections = [int(s.strip()) for s in user_input.split()]
                
                # 선택 검증
                if not selections or len(selections) > 3 or not all(1 <= s <= len(INFRA_TYPES) for s in selections):
                    print(f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)")
                    continue
                
                # 선택한 인프라 저장 (가중치: 1순위=5, 2순위=3, 3순위=1)
                weights = [5, 3, 1]
                selected_infra_types = []
                for i, selection in enumerate(selections):
                    if i < len(weights):  # 최대 3개까지만 처리
                        infra_type = INFRA_TYPES[selection-1]["code"]
                        user_infra_preferences[infra_type] = weights[i]
                        selected_infra_types.append(infra_type)
                
                # 사용자 입력 처리 후 응답 및 요약
                print(f"\n🤖 챗봇: 선택한 인프라를 저장했습니다.")
                print_summary(chatbot.user_state, user_infra_preferences)
                
                # 인프라별 세부 질문으로 전환
                setup_stage = "infra_details"
                current_infra_index = 0
                current_question_index = 0
                
                if selected_infra_types:
                    current_infra_type = selected_infra_types[current_infra_index]
                    # 첫 번째 인프라의 첫 번째 질문 출력
                    if INFRA_DETAIL_QUESTIONS.get(current_infra_type):
                        infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == current_infra_type), current_infra_type)
                        print(f"\n🤖 챗봇: {infra_name}에 대한 추가 질문입니다.")
                        print(INFRA_DETAIL_QUESTIONS[current_infra_type][current_question_index])
                    else:
                        # 질문이 없으면 다음 단계로
                        setup_stage = "property_features"
                        print("\n🤖 챗봇: 이제 매물 특성에 대해 알려주세요.")
                        print(PROPERTY_FEATURE_QUESTIONS[0]["question"])
                        current_feature_index = 0

            except ValueError:
                print(f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)")
        
        # 인프라 세부 질문 처리
        elif setup_stage == "infra_details":
            # 사용자 응답 저장
            selected_infra_types = list(user_infra_preferences.keys())
            current_infra_type = selected_infra_types[current_infra_index]
            
            # 현재 인프라 유형의 현재 질문에 대한 응답 저장
            infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == current_infra_type), current_infra_type)
            question = INFRA_DETAIL_QUESTIONS[current_infra_type][current_question_index]
            chatbot.user_state.update(f"infra_detail_{current_infra_type}_{current_question_index}", user_input)
            
            # 다음 질문으로 이동
            current_question_index += 1
            
            # 현재 인프라 유형의 모든 질문을 완료했는지 확인
            if current_question_index >= len(INFRA_DETAIL_QUESTIONS[current_infra_type]):
                # 다음 인프라 유형으로 이동
                current_infra_index += 1
                current_question_index = 0
                
                # 모든 인프라 유형에 대한 질문을 완료했는지 확인
                if current_infra_index >= len(selected_infra_types):
                    # 매물 특성 질문으로 이동
                    setup_stage = "property_features"
                    print("\n🤖 챗봇: 이제 매물 특성에 대해 알려주세요.")
                    print(PROPERTY_FEATURE_QUESTIONS[0]["question"])
                    current_feature_index = 0
                else:
                    # 다음 인프라 유형의 첫 번째 질문 출력
                    current_infra_type = selected_infra_types[current_infra_index]
                    infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == current_infra_type), current_infra_type)
                    print(f"\n🤖 챗봇: {infra_name}에 대한 추가 질문입니다.")
                    print(INFRA_DETAIL_QUESTIONS[current_infra_type][current_question_index])
            else:
                # 현재 인프라 유형의 다음 질문 출력
                print(f"\n🤖 챗봇: {INFRA_DETAIL_QUESTIONS[current_infra_type][current_question_index]}")
        
        # 매물 특성 질문 처리
        elif setup_stage == "property_features":
            # 사용자 응답 저장
            if current_feature_index < len(PROPERTY_FEATURE_QUESTIONS):
                feature_code = PROPERTY_FEATURE_QUESTIONS[current_feature_index]["code"]
                chatbot.user_state.update(f"feature_{feature_code}", user_input)
                
                # 다음 질문으로 이동
                current_feature_index += 1
                if current_feature_index < len(PROPERTY_FEATURE_QUESTIONS):
                    print(f"\n🤖 챗봇: {PROPERTY_FEATURE_QUESTIONS[current_feature_index]['question']}")
                else:
                    # 모든 매물 특성 질문 완료
                    setup_stage = "complete"
                    chatbot.setup_complete = True
                    chatbot.user_state.update("infra_preferences", user_infra_preferences)
                    
                    # 추천 결과 출력
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
                            if recommendations["combined"]:
                                result += "**종합 추천 매물 (위치+예산+인프라)**\n"
                            for i, prop in enumerate(recommendations["combined"], 1):
                                infra_score = prop.get("infra_score", 0)
                                result += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                                
                                # 인프라 세부 정보 추가
                                if prop.get("infra_details"):
                                    result += "   인프라 세부 정보:\n"
                                    for infra_type, detail in prop["infra_details"].items():
                                        if detail.get("score", 0) > 0:
                                            infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type)
                                            result += f"   - {infra_name}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
                            result += "\n추천 매물에 대해 더 알고 싶으신 내용이 있으신가요? (예: '1번 매물에 대해 자세히 알려줘')"
                        print(f"\n🤖 챗봇: {result}")
                        
                        # 대화 이력에 추가
                        chatbot.user_state.add_to_history("설정 완료", result)
                    except Exception as e:
                        print(f"\n🤖 챗봇: 추천 매물을 가져오는 중 오류가 발생했습니다: {e}")
                        print("\n🤖 챗봇: 죄송합니다. 매물 검색 중 문제가 발생했습니다.")
                        setup_stage = "complete"  # 설정은 완료 상태로 변경
                        chatbot.setup_complete = True
        
        # 설정 완료 후 일반 대화
        elif setup_stage == "complete":
            response = chatbot.process_message(user_input)
            print(f"\n🤖 챗봇: {response}")

if __name__ == "__main__":
    main()