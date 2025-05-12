from flask import Flask
from api import api_bp
import argparse
import os
from chatbot import RealEstateChatbot
from config import INFRA_TYPES, INFRA_DETAIL_QUESTIONS, PROPERTY_FEATURE_QUESTIONS
from utils import print_summary

def create_app():
    app = Flask(__name__)
    
    # API 블루프린트 등록
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return "부동산 추천 API 서버가 실행 중입니다."
    
    return app

def run_cli():
    """CLI 모드 실행"""
    parser = argparse.ArgumentParser(description='부동산 매물 추천 챗봇')
    parser.add_argument('--uuid', help='사용자 UUID')
    parser.add_argument('--reset', action='store_true', help='설정 초기화')
    args = parser.parse_args()
    
    user_uuid = args.uuid
    reset_settings = args.reset
    
    # UUID가 제공되지 않은 경우 입력 요청
    if not user_uuid:
        user_uuid = input("사용자 UUID를 입력하세요 (빈 값 입력시 기본값 사용): ")
        if not user_uuid.strip():
            user_uuid = None
    
    print("🏠 부동산 매물 추천 챗봇을 시작합니다.")
    
    # 챗봇 생성
    chatbot = RealEstateChatbot(user_uuid)
    
    # UUID가 있든 없든 항상 설정 단계 시작
    # 예산 관련 변수
    budget_names = {'rent': '월세', 'deposit': '보증금', 'maint': '관리비'}
    current_key = 'rent'
    cur = chatbot.user_state.get(current_key)
    
    # 설정 시작
    setup_stage = "budget"
    print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
   
    # 사용자 인프라 선호도 저장
    user_infra_preferences = {}
    
    # 필요한 변수 초기화
    current_infra_index = 0
    current_question_index = 0
    current_feature_index = 0
    selected_infra_types = []

    # 대화 반복
    while True:
        if setup_stage == "complete":
            user_input = input("\n🙋 사용자: ")
            if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
                print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
                break
            
            # 챗봇 응답 처리
            response = chatbot.process_message(user_input)
            print(f"\n🤖 챗봇: {response}")
            continue
        
        # 예산 설정 단계
        if setup_stage == "budget":
            user_input = input("\n🙋 사용자: ")
            if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
                print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
                break
            
            if current_key == 'rent':
                if user_input.lower() not in ["없음", "기본"]:
                    num = ''.join(filter(str.isdigit, user_input))
                    if num:
                        chatbot.user_state.update("rent", int(num))
                        # 사용자 입력 처리 후 응답 및 요약
                        print(f"\n🤖 챗봇: {num}만원으로 설정했습니다.")
                        print_summary(chatbot)
                
                # 다음 질문
                current_key = 'deposit'
                cur = chatbot.user_state.get(current_key)
                print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
                continue
            
            elif current_key == 'deposit':
                if user_input.lower() not in ["없음", "기본"]:
                    num = ''.join(filter(str.isdigit, user_input))
                    if num:
                        chatbot.user_state.update("deposit", int(num))
                        # 사용자 입력 처리 후 응답 및 요약
                        print(f"\n🤖 챗봇: {num}만원으로 설정했습니다.")
                        print_summary(chatbot)
                
                # 다음 질문
                current_key = 'maint'
                cur = chatbot.user_state.get(current_key)
                print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
                continue
            
            elif current_key == 'maint':
                if user_input.lower() not in ["없음", "기본"]:
                    num = ''.join(filter(str.isdigit, user_input))
                    if num:
                        chatbot.user_state.update("maint", int(num))
                        # 사용자 입력 처리 후 응답 및 요약
                        print(f"\n🤖 챗봇: {num}만원으로 설정했습니다.")
                        print_summary(chatbot)
                
                # 예산 설정 완료 후 다음 질문
                print("\n🤖 챗봇: 어떤 기준으로 추천할까요?")
                print("1. 소요시간 기준")
                print("2. 반경 기준 (m 단위)")
                print("3. 상관없음")
                
                current_key = 'service'
                setup_stage = "location"
                continue
        
        # 위치 기준 설정 단계
        elif setup_stage == "location":
            user_input = input("\n🙋 사용자: ")
            if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
                print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
                break
            
            if current_key == 'service':
                # 부분 문자열 검사로 더 유연하게 처리
                ui = user_input.strip().lower()
                old_service = chatbot.user_state.get("service")  # 기존 서비스 유형 저장

                if "소요" in ui or ui == "1":
                    service = "소요시간"
                elif "반경" in ui or ui == "2" or "반경" in ui:  # "반경이요"도 인식하도록 수정
                    service = "반경"
                elif "상관" in ui or ui == "3":
                    service = "상관없음"
                else:
                    print(f"\n🤖 챗봇: '{user_input}'이(가) 어떤 기준인지 명확하지 않습니다. 1.소요시간 2.반경 3.상관없음 중에서 선택해주세요.")
                    continue

                # 서비스 유형이 변경된 경우 관련 설정 초기화
                if old_service != service:
                    # 기존 설정과 다른 경우에만 초기화
                    if service == "소요시간":
                        # 반경 관련 설정 초기화
                        chatbot.user_state.update("radius", None)
                        print(f"\n🤖 챗봇: 서비스 유형이 변경되어 반경 설정이 초기화되었습니다.")
                    elif service == "반경":
                        # 소요시간 관련 설정 초기화
                        chatbot.user_state.update("time_limit", None)
                        chatbot.user_state.update("movement", None)
                        print(f"\n🤖 챗봇: 서비스 유형이 변경되어 소요시간 설정이 초기화되었습니다.")
                    elif service == "상관없음":
                        # 소요시간, 반경 모두 초기화
                        chatbot.user_state.update("time_limit", None)
                        chatbot.user_state.update("movement", None)
                        chatbot.user_state.update("radius", None)
                        print(f"\n🤖 챗봇: 서비스 유형이 변경되어 위치 관련 설정이 초기화되었습니다.")

                # 서비스 저장 및 요약 출력
                chatbot.user_state.update("service", service)
                print(f"\n🤖 챗봇: {service} 기준으로 설정했습니다.")
                print_summary(chatbot)

                # 다음 단계 분기
                if service == "소요시간":
                    print("\n🤖 챗봇: 이동 방법? 1.도보 2.대중교통 3.상관없음")
                    current_key = 'movement'
                elif service == "반경":
                    print("\n🤖 챗봇: 반경(m)을 입력하세요")
                    current_key = 'radius'
                else:  # 상관없음
                    chatbot.user_state.update("movement", "상관없음")
                    setup_stage = "infra"
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
                print_summary(chatbot)
                
                print("\n🤖 챗봇: 최대 몇 분 이내를 원하시나요?")
                current_key = 'time_limit'
                continue
            
            elif current_key == 'time_limit':
                try:
                    time_value = int(''.join(filter(str.isdigit, user_input)))
                    chatbot.user_state.update("time_limit", time_value)
                    
                    # 사용자 입력 처리 후 응답 및 요약
                    print(f"\n🤖 챗봇: {time_value}분 이내로 설정했습니다.")
                    print_summary(chatbot)
                    
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
                    print_summary(chatbot)
                    
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
            user_input = input("\n🙋 사용자: ")
            if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
                print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
                break
            
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
                chatbot.user_state.update("infra_preferences", user_infra_preferences)
                print_summary(chatbot, user_infra_preferences)
                
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
            user_input = input("\n🙋 사용자: ")
            if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
                print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
                break
            
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
            user_input = input("\n🙋 사용자: ")
            if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
                print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
                break
            
            # 사용자 응답 저장 - 이 부분이 if문 안에 정확히 들어와야 함
            if current_feature_index < len(PROPERTY_FEATURE_QUESTIONS):
                feature_code = PROPERTY_FEATURE_QUESTIONS[current_feature_index]["code"]
                chatbot.user_state.update(f"feature_{feature_code}", user_input)
                
                # 다음 질문으로 이동
                current_feature_index += 1
                if current_feature_index < len(PROPERTY_FEATURE_QUESTIONS):
                    print(f"\n🤖 챗봇: {PROPERTY_FEATURE_QUESTIONS[current_feature_index]['question']}")
                else:
                    # 모든 매물 특성 질문 완료, 추천 매물 표시 후 종료
                    setup_stage = "complete"
                    chatbot.setup_complete = True

                    print("\n🤖 챗봇: 설정이 완료되었습니다. 추천 매물을 찾고 있습니다...")

                    # 인프라 선호도 저장
                    chatbot.user_state.update("infra_preferences", user_infra_preferences)

                    # 매물 정보 출력 함수 정의
                    def print_property(index, prop, detailed=True, user_preferences=None):
                        """매물 정보 출력 함수 (사용자 선호도 강조)"""
                        infra_score = prop.get("infra_score", 0)
                        stars = min(5, max(1, round(infra_score)))  # 1~5 사이의 별 표시
                        
                        # 면적 정보 추출 및 변환
                        size = prop.get('size', 0)
                        if isinstance(size, str) and size.strip():
                            try:
                                size = float(''.join(c for c in size if c.isdigit() or c == '.'))
                            except:
                                size = 0
                        
                        # 기본 정보 출력
                        print(f"\n  {index}. 📌 {prop.get('address', '주소 정보 없음')} ({prop.get('station', '역 정보 없음')})")
                        print(f"     💸 월세: {prop.get('rent', 0)}만원 | 보증금: {prop.get('deposit', 0)}만원 | 관리비: {prop.get('maint', 0)}만원")
                        print(f"     🚶 {prop.get('time_info', '시간 정보 없음')} | 인프라 점수: {'⭐' * stars}")
                        
                        if detailed:
                            # 층수 정보 변환
                            floor = prop.get('floor', '정보 없음')
                            floor_num = 0
                            try:
                                floor_num = int(''.join(filter(str.isdigit, floor)))
                            except:
                                pass
                            
                            # 층수 구분
                            floor_category = "정보 없음"
                            if "반지" in floor.lower() or "지하" in floor.lower():
                                floor_category = "반지하"
                            elif 1 <= floor_num <= 3:
                                floor_category = "저층"
                            elif 4 <= floor_num <= 7:
                                floor_category = "중층"
                            elif floor_num >= 8:
                                floor_category = "고층"
                            
                            # 사용자 선호도에 맞는지 확인
                            if user_preferences:
                                feature_prefs = user_preferences.get("property_features", {})
                                
                                # 층수 일치 여부
                                floor_pref = feature_prefs.get("floor", "").lower()
                                floor_match = True
                                
                                if floor_pref and floor_pref != "상관없음":
                                    if "저층" in floor_pref:
                                        floor_match = floor_category == "저층"
                                    elif "중층" in floor_pref:
                                        floor_match = floor_category == "중층"
                                    elif "고층" in floor_pref:
                                        floor_match = floor_category == "고층"
                                    elif "반지하 제외" in floor_pref:
                                        floor_match = floor_category != "반지하"
                                
                                floor_icon = "✓" if floor_match else "✗"
                                
                                # 면적 일치 여부
                                size_pref = feature_prefs.get("size", "").lower()
                                size_match = True
                                
                                if size_pref and size_pref != "상관없음":
                                    if "5평 이하" in size_pref:
                                        size_match = size <= 5
                                    elif "5~10평" in size_pref:
                                        size_match = 5 <= size <= 10
                                    elif "10~15평" in size_pref:
                                        size_match = 10 <= size <= 15
                                    elif "15~20평" in size_pref:
                                        size_match = 15 <= size <= 20
                                    elif "20평 이상" in size_pref:
                                        size_match = size >= 20
                                
                                size_icon = "✓" if size_match else "✗"
                                
                                # 난방 방식 일치 여부
                                heating = prop.get('heating_type', prop.get('난방', '정보 없음'))
                                heating_pref = feature_prefs.get("heating", "").lower()
                                heating_match = True
                                
                                if heating_pref and heating_pref != "상관없음":
                                    if "개별난방" in heating_pref:
                                        heating_match = "개별" in heating.lower()
                                    elif "중앙난방" in heating_pref:
                                        heating_match = "중앙" in heating.lower()
                                    elif "지역난방" in heating_pref:
                                        heating_match = "지역" in heating.lower()
                                
                                heating_icon = "✓" if heating_match else "✗"
                                
                                # 주차 가능 여부
                                parking_text = prop.get('parking', "")
                                if isinstance(parking_text, str):
                                    parking = "있" in parking_text.lower() or "가능" in parking_text.lower()
                                else:
                                    parking = bool(parking_text)
                                    
                                parking_pref = feature_prefs.get("parking", "").lower()
                                parking_match = True
                                
                                if parking_pref and parking_pref != "상관없음":
                                    parking_required = ("있" in parking_pref or "중요" in parking_pref or 
                                                    "네" in parking_pref or "필요" in parking_pref)
                                    if parking_required:
                                        parking_match = parking
                                
                                parking_icon = "✓" if parking_match else "✗"
                                parking_display = "가능" if parking else "불가능"
                                
                                # 엘리베이터 여부 - 중요한 수정 부분
                                elevator_text = prop.get('엘리베이터', '정보 없음')
                                elevator = "있" in str(elevator_text).lower() or "가능" in str(elevator_text).lower()
                                
                                elevator_pref = feature_prefs.get("elevator", "").lower()
                                elevator_match = True
                                
                                if elevator_pref and elevator_pref != "상관없음":
                                    elevator_required = ("있" in elevator_pref or "중요" in elevator_pref or 
                                                    "네" in elevator_pref or "필요" in elevator_pref)
                                    if elevator_required:
                                        elevator_match = elevator
                                
                                elevator_icon = "✓" if elevator_match else "✗"
                                elevator_display = "있음" if elevator else "없음"
                                
                                # 방향 일치 여부
                                direction = prop.get('view', prop.get('direction', '정보 없음')).lower()
                                direction_pref = feature_prefs.get("direction", "").lower()
                                direction_match = True
                                
                                if direction_pref and direction_pref != "상관없음":
                                    if "남향" in direction_pref:
                                        direction_match = "남" in direction
                                    elif "동향" in direction_pref:
                                        direction_match = "동" in direction
                                    elif "서향" in direction_pref:
                                        direction_match = "서" in direction
                                    elif "북향" in direction_pref:
                                        direction_match = "북" in direction
                                
                                direction_icon = "✓" if direction_match else "✗"
                                
                                # 매물 정보 출력
                                print(f"     🏢 층수: {floor} ({floor_category}) {floor_icon} | 면적: {size}평 {size_icon}")
                                print(f"     🔥 난방: {heating} {heating_icon} | 방향: {prop.get('view', prop.get('direction', '정보 없음'))} {direction_icon}")
                                print(f"     🅿️ 주차: {parking_display} {parking_icon} | 엘리베이터: {elevator_display} {elevator_icon}")
                            else:
                                # 기본 출력 방식 (선호도 체크 없음)
                                print(f"     🏢 층수: {floor} ({floor_category}) | 면적: {size}평")
                                print(f"     🔥 난방: {prop.get('heating_type', prop.get('난방', '정보 없음'))} | 방향: {prop.get('view', prop.get('direction', '정보 없음'))}")
                                parking_display = "가능" if prop.get('parking', False) else "불가능"
                                elevator_text = prop.get('엘리베이터', '정보 없음')
                                elevator_display = "있음" if "있" in str(elevator_text).lower() else "없음"
                                print(f"     🅿️ 주차: {parking_display} | 엘리베이터: {elevator_display}")
                            
                            # 시설 정보
                            if prop.get('facilities', prop.get('생활시설', '')):
                                facilities = prop.get('facilities', prop.get('생활시설', ''))
                                if facilities and facilities != "시설 정보 없음":
                                    print(f"     🛋️ 시설: {facilities}")
                            
                            # 안전시설 정보
                            if prop.get('안전시설'):
                                safety = prop.get('안전시설')
                                if safety and safety != "정보 없음":
                                    print(f"     🔒 안전: {safety}")
                            
                            # 주변 인프라 정보 출력
                            if prop.get("infra_details"):
                                near_infras = []
                                
                                # 각 인프라 유형별 정보
                                for infra_type, detail in prop.get("infra_details", {}).items():
                                    if detail and detail.get("nearest"):
                                        # 인프라 이름과 코드 매핑
                                        try:
                                            from config import INFRA_TYPES
                                            infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type)
                                        except:
                                            infra_name = infra_type.replace("_", " ").title()
                                        
                                        distance = detail.get("distance", 0)
                                        nearest = detail.get("nearest", "")
                                        
                                        # 5km 이내 인프라만 표시
                                        if nearest and distance > 0 and distance < 5000:
                                            near_infras.append((infra_name, nearest, distance))
                                
                                # 거리순 정렬
                                near_infras.sort(key=lambda x: x[2])
                                
                                if near_infras:
                                    print("     📊 주변 인프라:")
                                    for infra_name, nearest, distance in near_infras:
                                        print(f"       - {infra_name}: {nearest} ({distance:.0f}m)")
                                else:
                                    print("     📊 주변 인프라: 가까운 시설 없음")
                            else:
                                print("     📊 주변 인프라: 정보 없음")

                    # 추천 결과 가져오기
                    try:
                        recommendations = chatbot.recommender.get_recommendations()
                        
                        # 추천 매물을 DB에 저장 시도
                        try:
                            # 속성이 존재하는지 확인
                            if hasattr(chatbot.user_state, 'save_recommendations_to_db'):
                                db_save_result = chatbot.user_state.save_recommendations_to_db(recommendations)
                                if db_save_result:
                                    print("📊 추천 매물이 DB에 성공적으로 저장되었습니다.")
                            else:
                                print("⚠️ DB 저장 기능을 사용할 수 없습니다. 결과는 화면에만 표시됩니다.")
                        except Exception as db_error:
                            print(f"⚠️ DB 저장 중 오류 발생: {db_error}")
                        
                        # 결과 출력 형식 개선
                        print("\n" + "="*60)
                        print("📋 추천 매물 정보 요약")
                        print("="*60)

                        # 예산 정보 요약
                        print("\n💰 [예산 정보]")
                        print(f"  월세: {chatbot.user_state.get('rent')}만원")
                        print(f"  보증금: {chatbot.user_state.get('deposit')}만원")
                        print(f"  관리비: {chatbot.user_state.get('maint')}만원")

                        # 거주지 정보 요약
                        print("\n📍 [거주지 정보]")
                        if chatbot.user_state.get('service') == "반경":
                            print(f"  반경: {chatbot.user_state.get('radius')}m")
                        elif chatbot.user_state.get('service') == "소요시간":
                            print(f"  소요시간: {chatbot.user_state.get('time_limit')}분 ({chatbot.user_state.get('movement')})")
                        print(f"  주소: {chatbot.user_state.get('address', '설정된 주소 없음')}")
                        print(f"  선호 지역: {chatbot.user_state.get('preferred_area', '설정된 선호 지역 없음')}")

                        # 추천 매물이 있는지 확인
                        has_recommendations = (
                            recommendations.get("combined") or 
                            recommendations.get("location_based") or 
                            recommendations.get("budget_based")
                        )

                        if has_recommendations:
                            # 종합 추천 매물 출력
                            if recommendations.get("combined", []):
                                print("\n🏠 [종합 추천 매물]")
                                
                                # 소프트 스코어링 로직을 반영하여 하드 필터링 제거
                                # (기존 코드는 엘리베이터 선호도를 하드 필터로 적용)
                                
                                # total_score 기준으로 정렬 (기존에 추가된 경우)
                                sorted_properties = sorted(
                                    recommendations["combined"], 
                                    key=lambda x: x.get("total_score", x.get("infra_score", 0)),
                                    reverse=True
                                )
                                
                                # total_score가 없는 경우를 대비해 feature_score를 계산하고 total_score 추가
                                for prop in sorted_properties:
                                    if "total_score" not in prop:
                                        # 엘리베이터 점수
                                        elevator_text = str(prop.get('엘리베이터', "")).lower()
                                        elevator_exists = "있" in elevator_text or "가능" in elevator_text
                                        
                                        # 주차 점수
                                        parking = prop.get("parking", False)
                                        
                                        # feature_score 계산
                                        feature_score = 0
                                        if elevator_exists:
                                            feature_score += 1
                                        if parking:
                                            feature_score += 1
                                        
                                        # 점수 저장
                                        prop["feature_score"] = feature_score
                                        prop["total_score"] = prop.get("infra_score", 0) + feature_score
                                
                                # 필터링된 매물 출력
                                if sorted_properties:
                                    for i, prop in enumerate(sorted_properties[:5], 1):
                                        # 소프트 스코어링 정보 출력 (선택적)
                                        feature_score = prop.get("feature_score", 0)
                                        features = []
                                        if "있" in str(prop.get('엘리베이터', "")).lower():
                                            features.append("엘리베이터(+1)")
                                        if prop.get("parking", False):
                                            features.append("주차(+1)")
                                        
                                        feature_info = f" | 특성 점수: {feature_score}점" + (f" ({', '.join(features)})" if features else "")
                                        print(f"  # 매물 {i} - 총점: {prop.get('total_score', prop.get('infra_score', 0)):.1f}{feature_info}")
                                        
                                        # 기존 출력 함수 호출
                                        print_property(i, prop, detailed=True, user_preferences=chatbot.user_state.state)
                                else:
                                    print("⚠️ 조건에 맞는 매물이 없습니다. 설정을 변경해보세요.")

                            # 거주지 기반 추천 매물 출력
                            if recommendations.get("location_based", []):
                                print("\n🏠 [거주지 기반 추천 매물]")
                                for i, prop in enumerate(recommendations["location_based"][:3], 1):
                                    print_property(i, prop, detailed=False, user_preferences=chatbot.user_state.state)

                            # 예산 기반 추천 매물 출력
                            if recommendations.get("budget_based", []):
                                print("\n🏠 [예산 기반 추천 매물]")
                                for i, prop in enumerate(recommendations["budget_based"][:3], 1):
                                    print_property(i, prop, detailed=False, user_preferences=chatbot.user_state.state)
                        else:
                            print("\n❗ 현재 설정하신 조건에 맞는 매물을 찾지 못했습니다.")
                            print("\n💡 추천 사항:")
                            print("  1. 예산 범위를 넓혀보세요 (월세, 보증금 상향 조정)")
                            print("  2. 검색 반경을 넓혀보세요 (현재 반경 → 더 넓은 범위)")
                            print("  3. 다른 지역도 고려해보세요")

                        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
                        
                    except Exception as e:
                        print(f"\n❌ 추천 매물을 가져오는 중 오류가 발생했습니다: {e}")
                        
                        # 기본 매물 정보 출력
                        print("\n📝 기본 매물 정보를 대신 제공합니다:")
                        
                        default_properties = [
                            {
                                "address": "서울 강남구 역삼동 123-45",
                                "station": "강남역",
                                "rent": 95,
                                "deposit": 500,
                                "maint": 10,
                                "time_info": "도보 5분",
                                "floor": "5층",
                                "heating_type": "개별난방",
                                "parking": True,
                                "infra_score": 2.5
                            },
                            {
                                "address": "서울 마포구 합정동 456-78",
                                "station": "합정역",
                                "rent": 85,
                                "deposit": 300,
                                "maint": 8,
                                "time_info": "도보 7분",
                                "floor": "3층",
                                "heating_type": "중앙난방",
                                "parking": False,
                                "infra_score": 3.0
                            }
                        ]
                        
                        for i, prop in enumerate(default_properties, 1):
                            print_property(i, prop, detailed=True)
                        
                        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")

                    # 챗봇 종료
                    break

if __name__ == '__main__':
    # 환경 변수 MODE가 'api'인 경우 API 서버 실행, 그렇지 않으면 CLI 모드 실행
    mode = os.getenv('MODE', 'cli')
    
    if mode.lower() == 'api':
        app = create_app()
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # CLI 모드 실행
        run_cli()