from flask import Flask
from api import api_bp
import argparse
import os
from chatbot import RealEstateChatbot
from config import INFRA_TYPES, INFRA_DETAIL_QUESTIONS, PROPERTY_FEATURE_QUESTIONS
from utils import print_summary
from chatbot import RealEstateChatbot, setup_infrastructure_v2

def create_app():
    app = Flask(__name__)
    
    # CORS 설정
    @app.after_request
    def add_cors_headers(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS')
        return response
    
    # API 블루프린트 등록
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return "부동산 추천 API 서버가 실행 중입니다."
    
    return app

def print_property(index, prop, detailed=True, user_preferences=None):
    """매물 정보 출력 함수 (사용자 선호도 강조)"""
    # 중복 출력 방지를 위해 이미 처리한 속성을 추적
    processed_attributes = set()
    
    # 기본 정보
    infra_score = prop.get("infra_score", 0)
    feature_score = prop.get("feature_score", 0)
    total_score = prop.get("total_score", 0)
    feature_details = prop.get("feature_score_details", [])
    
    # 기본 정보 출력
    print(f"\n  {index}. 📌 {prop.get('address', '주소 정보 없음')} ({prop.get('station', '역 정보 없음')})")
    print(f"     💸 월세: {prop.get('rent', 0)}만원 | 보증금: {prop.get('deposit', 0)}만원 | 관리비: {prop.get('maint', 0)}만원")
    print(f"     🚶 {prop.get('time_info', '시간 정보 없음')}")
    print(f"     ⭐ 총점: {total_score:.1f}/10.0 = 인프라({infra_score:.1f}/3.0) + 특성({feature_score:.1f}/7.0)")
    
    if feature_details:
        print(f"     📊 특성 점수: {', '.join(feature_details)}")
    
    if detailed:
        # 층수 정보
        floor_str = prop.get('floor', '정보 없음')
        processed_attributes.add('floor')
        
        # 층수 카테고리 결정
        floor_category = "정보 없음"
        if any(term in floor_str.lower() for term in ["반지하", "반지층", "반층", "지하"]):
            floor_category = "반지하/반층"
        elif "옥탑" in floor_str.lower():
            floor_category = "옥탑"
        else:
            try:
                floor_num = int(''.join(filter(str.isdigit, floor_str)))
                if 1 <= floor_num <= 3:
                    floor_category = "저층(1-3층)"
                elif 4 <= floor_num <= 7:
                    floor_category = "중층(4-7층)"
                elif floor_num >= 8:
                    floor_category = "고층(8층 이상)"
            except:
                pass
        
        # 타입 정보 추출 (타입은 출력은 하되 점수에는 반영하지 않음)
        room_type = prop.get('type', '정보 없음')
        processed_attributes.add('type')
        
        # 면적 정보
        size = prop.get('size', 0)
        processed_attributes.add('size')
        if isinstance(size, str) and size.strip():
            try:
                size = float(''.join(c for c in size if c.isdigit() or c == '.'))
            except:
                size = 0
        
        # 사용자 선호도에 맞는지 확인
        if user_preferences:
            feature_prefs = user_preferences.get("property_features", {})
            
            # 층수, 면적, 방향, 타입 일치 여부 확인
            preferences_match = check_preferences_match(prop, feature_prefs, floor_category)
            
            # 이미 처리한 속성 추적하여 중복 방지
            processed_attributes.add('heating_type')
            processed_attributes.add('view')
            processed_attributes.add('direction')
            processed_attributes.add('parking')
            processed_attributes.add('엘리베이터')
            
            # 매물 세부 정보 출력
            print(f"     🏢 층수: {floor_str} ({floor_category}) {preferences_match['floor_icon']} | 면적: {size}평 {preferences_match['size_icon']}")
            print(f"     🔥 난방: {prop.get('heating_type', prop.get('난방', '정보 없음'))} {preferences_match['heating_icon']} | "
                  f"방향: {prop.get('view', prop.get('direction', '정보 없음'))} {preferences_match['direction_icon']}")
            print(f"     🅿️ 주차: {preferences_match['parking_display']} {preferences_match['parking_icon']} | "
                  f"엘리베이터: {preferences_match['elevator_display']} {preferences_match['elevator_icon']}")
            print(f"     🏠 타입: {room_type} {preferences_match.get('type_icon', '')}")
        else:
            # 기본 출력 방식 (선호도 체크 없음)
            print(f"     🏢 층수: {floor_str} ({floor_category}) | 면적: {size}평")
            print(f"     🔥 난방: {prop.get('heating_type', prop.get('난방', '정보 없음'))} | 방향: {prop.get('view', prop.get('direction', '정보 없음'))}")
            parking_display = "가능" if prop.get('parking', False) else "불가능"
            elevator_text = prop.get('엘리베이터', '정보 없음')
            elevator_display = "있음" if "있" in str(elevator_text).lower() else "없음"
            print(f"     🅿️ 주차: {parking_display} | 엘리베이터: {elevator_display}")
            print(f"     🏠 타입: {room_type}")

        # 시설 정보
        if prop.get('facilities', prop.get('생활시설', '')):
            facilities = prop.get('facilities', prop.get('생활시설', ''))
            processed_attributes.add('facilities')
            processed_attributes.add('생활시설')
            if facilities and facilities != "시설 정보 없음":
                print(f"     🛋️ 시설: {facilities}")
        
        # 안전시설 정보
        if prop.get('안전시설'):
            safety = prop.get('안전시설')
            processed_attributes.add('안전시설')
            if safety and safety != "정보 없음":
                print(f"     🔒 안전: {safety}")
        
        # 주변 인프라 정보 출력
        display_nearby_infrastructure(prop)

def check_preferences_match(prop, feature_prefs, floor_category=None):
    """사용자 선호도 일치 여부 확인"""
    result = {}
    
    # 층수 카테고리 결정 (전달받지 않은 경우)
    if floor_category is None:
        floor_str = prop.get('floor', '').lower()
        if any(term in floor_str for term in ["반지하", "반지층", "반층", "지하"]):
            floor_category = "반지하/반층"
        elif "옥탑" in floor_str:
            floor_category = "옥탑"
        else:
            try:
                floor_num = int(''.join(filter(str.isdigit, floor_str)))
                if 1 <= floor_num <= 3:
                    floor_category = "저층(1-3층)"
                elif 4 <= floor_num <= 7:
                    floor_category = "중층(4-7층)"
                elif floor_num >= 8:
                    floor_category = "고층(8층 이상)"
            except:
                floor_category = "정보 없음"
    
    # 1. 층수 일치 여부
    floor_pref = feature_prefs.get("floor", "").lower()
    floor_match = True
    if floor_pref and floor_pref != "상관없음":
        if "2층 이상" in floor_pref:
            try:
                floor_num = int(''.join(filter(str.isdigit, prop.get('floor', '0'))))
                floor_match = floor_num >= 2
            except:
                floor_match = False
        elif "저층" in floor_pref:
            floor_match = "저층" in floor_category
        elif "중층" in floor_pref:
            floor_match = "중층" in floor_category
        elif "고층" in floor_pref:
            floor_match = "고층" in floor_category
        elif "반지하 제외" in floor_pref:
            floor_match = "반지하" not in floor_category and "반층" not in floor_category
    result['floor_icon'] = "✓" if floor_match else "✗"
    
    # 2. 면적 일치 여부
    size_pref = feature_prefs.get("size", "").lower()
    size_match = True
    size = prop.get('size', 0)
    if isinstance(size, str) and size.strip():
        try:
            size = float(''.join(c for c in size if c.isdigit() or c == '.'))
        except:
            size = 0
    
    if size_pref and size_pref != "상관없음":
        if "10평 이하" in size_pref:
            size_match = size <= 10
        elif "5평 이하" in size_pref:
            size_match = size <= 5
        elif "5~10평" in size_pref:
            size_match = 5 <= size <= 10
        elif "10~15평" in size_pref:
            size_match = 10 <= size <= 15
        elif "15~20평" in size_pref:
            size_match = 15 <= size <= 20
        elif "20평 이상" in size_pref:
            size_match = size >= 20
    result['size_icon'] = "✓" if size_match else "✗"
    
    # 3. 난방 방식 일치 여부
    heating = prop.get('heating_type', prop.get('난방', '정보 없음')).lower()
    heating_pref = feature_prefs.get("heating", "").lower()
    heating_match = True
    if heating_pref and heating_pref != "상관없음":
        if "개별난방" in heating_pref:
            heating_match = "개별" in heating
        elif "중앙난방" in heating_pref:
            heating_match = "중앙" in heating
        elif "지역난방" in heating_pref:
            heating_match = "지역" in heating
    result['heating_icon'] = "✓" if heating_match else "✗"
    
    # 4. 주차 가능 여부
    parking_text = prop.get('parking', "")
    parking = "있" in str(parking_text).lower() or "가능" in str(parking_text).lower() or parking_text is True
    parking_pref = feature_prefs.get("parking", "").lower()
    parking_match = True
    
    if parking_pref and parking_pref != "상관없음":
        if "네" in parking_pref or "있" in parking_pref or "중요" in parking_pref or "필요" in parking_pref:
            # 주차 필요함
            parking_match = parking
    
    result['parking_icon'] = "✓" if parking_match else "✗"
    result['parking_display'] = "가능" if parking else "불가능"
    
    # 5. 엘리베이터 여부
    elevator_text = prop.get('엘리베이터', '정보 없음')
    elevator = "있" in str(elevator_text).lower() or "가능" in str(elevator_text).lower()
    elevator_pref = feature_prefs.get("elevator", "").lower()
    elevator_match = True
    
    if elevator_pref and elevator_pref != "상관없음":
        if "네" in elevator_pref or "있" in elevator_pref or "중요" in elevator_pref or "필요" in elevator_pref:
            # 엘리베이터 필요함
            elevator_match = elevator
    
    result['elevator_icon'] = "✓" if elevator_match else "✗"
    result['elevator_display'] = "있음" if elevator else "없음"
    
    # 6. 방향 일치 여부
    direction = prop.get('view', prop.get('direction', '정보 없음')).lower()
    direction_pref = feature_prefs.get("direction", "").lower()
    direction_match = True
    if direction_pref and direction_pref != "상관없음":
        if "남" in direction_pref:
            direction_match = "남" in direction
        elif "동" in direction_pref:
            direction_match = "동" in direction
        elif "서" in direction_pref:
            direction_match = "서" in direction
        elif "북" in direction_pref:
            direction_match = "북" in direction
    result['direction_icon'] = "✓" if direction_match else "✗"
    
    # 7. 타입 일치 여부
    room_type = prop.get('type', '정보 없음').lower()
    type_pref = feature_prefs.get("type", "").lower()
    type_match = True
    if type_pref and type_pref != "상관없음":
        if "원룸" in type_pref:
            type_match = "원룸" in room_type
        elif "투룸" in type_pref:
            type_match = "투룸" in room_type
    result['type_icon'] = "✓" if type_match else "✗"
    
    return result

def check_preferences(prop, feature_prefs, floor_category):
    """사용자 선호도와 매물 비교"""
    result = {}
    
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
    result['floor_icon'] = "✓" if floor_match else "✗"
    
    # 면적 일치 여부
    size_pref = feature_prefs.get("size", "").lower()
    size_match = True
    size = prop.get('size', 0)
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
    result['size_icon'] = "✓" if size_match else "✗"
    
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
    result['heating_icon'] = "✓" if heating_match else "✗"
    
    # 주차 가능 여부
    parking_text = prop.get('parking', "")
    parking = "있" in str(parking_text).lower() or "가능" in str(parking_text).lower()
    parking_pref = feature_prefs.get("parking", "").lower()
    parking_match = True
    if parking_pref and parking_pref != "상관없음":
        parking_required = ("있" in parking_pref or "중요" in parking_pref or 
                          "네" in parking_pref or "필요" in parking_pref)
        if parking_required:
            parking_match = parking
    result['parking_icon'] = "✓" if parking_match else "✗"
    result['parking_display'] = "가능" if parking else "불가능"
    
    # 엘리베이터 여부
    elevator_text = prop.get('엘리베이터', '정보 없음')
    elevator = "있" in str(elevator_text).lower() or "가능" in str(elevator_text).lower()
    elevator_pref = feature_prefs.get("elevator", "").lower()
    elevator_match = True
    if elevator_pref and elevator_pref != "상관없음":
        elevator_required = ("있" in elevator_pref or "중요" in elevator_pref or 
                          "네" in elevator_pref or "필요" in elevator_pref)
        if elevator_required:
            elevator_match = elevator
    result['elevator_icon'] = "✓" if elevator_match else "✗"
    result['elevator_display'] = "있음" if elevator else "없음"
    
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
    result['direction_icon'] = "✓" if direction_match else "✗"
    
    return result

def display_nearby_infrastructure(prop):
    """주변 인프라 정보 출력"""
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

def run_cli():
    """CLI 모드 실행"""
    parser = argparse.ArgumentParser(description='부동산 매물 추천 챗봇')
    parser.add_argument('--uuid', help='사용자 UUID')
    parser.add_argument('--reset', action='store_true', help='설정 초기화')
    args = parser.parse_args()
    
    user_uuid = args.uuid or input("사용자 UUID를 입력하세요 (빈 값 입력시 기본값 사용): ").strip() or None
    reset_settings = args.reset
    
    print("🏠 부동산 매물 추천 챗봇을 시작합니다.")
    
    # 챗봇 생성
    chatbot = RealEstateChatbot(user_uuid)
    
    # 설정 진행
    setup_chatbot(chatbot)
    
def setup_chatbot(chatbot):
    """챗봇 설정 과정 처리"""
    # 예산 설정
    setup_budget(chatbot)
    
    # 위치 기준 설정
    setup_location(chatbot)
    
    # 인프라 선호도 설정 (기존꺼)
    # user_infra_preferences = setup_infrastructure(chatbot)
    
    # 인프라 선호도 설정 (v2 버전 사용)
    setup_infrastructure_v2(chatbot)
    
    # 매물 특성 설정
    setup_property_features(chatbot)
    
    # 추천 매물 표시 및 처리
    display_recommendations(chatbot)

def setup_budget(chatbot):
    """예산 설정 처리"""
    budget_names = {'rent': '월세', 'deposit': '보증금', 'maint': '관리비'}
    budget_keys = list(budget_names.keys())
    
    for key in budget_keys:
        cur = chatbot.user_state.get(key)
        print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
        user_input = input("\n🙋 사용자: ")
        
        if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
            print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
            exit(0)
            
        if user_input.lower() not in ["없음", "기본"]:
            num = ''.join(filter(str.isdigit, user_input))
            if num:
                chatbot.user_state.update(key, int(num))
                print(f"\n🤖 챗봇: {num}만원으로 설정했습니다.")
                print_summary(chatbot)

def setup_location(chatbot):
    """위치 기준 설정 처리"""
    print("\n🤖 챗봇: 어떤 기준으로 추천할까요?")
    print("1. 소요시간 기준")
    print("2. 반경 기준 (m 단위)")
    print("3. 상관없음")
    
    user_input = input("\n🙋 사용자: ")
    
    if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
        exit(0)
    
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
        return setup_location(chatbot)

    # 서비스 유형이 변경된 경우 관련 설정 초기화
    if old_service != service:
        reset_location_settings(chatbot, service, old_service)

    # 서비스 저장 및 요약 출력
    chatbot.user_state.update("service", service)
    print(f"\n🤖 챗봇: {service} 기준으로 설정했습니다.")
    print_summary(chatbot)

    # 추가 설정
    if service == "소요시간":
        setup_movement(chatbot)
    elif service == "반경":
        setup_radius(chatbot)

def reset_location_settings(chatbot, new_service, old_service):
    """위치 관련 설정 초기화"""
    if new_service == "소요시간":
        # 반경 관련 설정 초기화
        chatbot.user_state.update("radius", None)
        print(f"\n🤖 챗봇: 서비스 유형이 변경되어 반경 설정이 초기화되었습니다.")
    elif new_service == "반경":
        # 소요시간 관련 설정 초기화
        chatbot.user_state.update("time_limit", None)
        chatbot.user_state.update("movement", None)
        print(f"\n🤖 챗봇: 서비스 유형이 변경되어 소요시간 설정이 초기화되었습니다.")
    elif new_service == "상관없음":
        # 소요시간, 반경 모두 초기화
        chatbot.user_state.update("time_limit", None)
        chatbot.user_state.update("movement", None)
        chatbot.user_state.update("radius", None)
        print(f"\n🤖 챗봇: 서비스 유형이 변경되어 위치 관련 설정이 초기화되었습니다.")

def setup_movement(chatbot):
    """이동 방법 설정"""
    print("\n🤖 챗봇: 이동 방법? 1.도보 2.대중교통 3.상관없음")
    user_input = input("\n🙋 사용자: ")
    
    if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
        exit(0)
    
    # 수정된 부분: 입력값 확인 로직 개선
    if user_input in ["1"] or "도보" in user_input:
        movement = "도보"
    elif user_input in ["2"] or "대중" in user_input or "교통" in user_input:
        movement = "대중교통"
    elif user_input in ["3"] or "상관" in user_input or "없" in user_input:
        movement = "상관없음"
    else:
        # 기본값
        movement = "도보"
        print(f"\n🤖 챗봇: 입력을 이해할 수 없어 기본값인 '도보'로 설정합니다.")
    
    chatbot.user_state.update("movement", movement)
    
    print(f"\n🤖 챗봇: 이동 방법을 '{movement}'(으)로 설정했습니다.")
    print_summary(chatbot)
    
    print("\n🤖 챗봇: 최대 몇 분 이내를 원하시나요?")
    setup_time_limit(chatbot)

def setup_time_limit(chatbot):
    """소요시간 제한 설정"""
    user_input = input("\n🙋 사용자: ")
    
    if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
        exit(0)
    
    try:
        time_value = int(''.join(filter(str.isdigit, user_input)))
        chatbot.user_state.update("time_limit", time_value)
        
        print(f"\n🤖 챗봇: {time_value}분 이내로 설정했습니다.")
        print_summary(chatbot)
    except:
        print("\n🤖 챗봇: 숫자로 입력해주세요.")
        return setup_time_limit(chatbot)

def setup_radius(chatbot):
    """반경 설정"""
    print("\n🤖 챗봇: 반경(m)을 입력하세요")
    user_input = input("\n🙋 사용자: ")
    
    if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
        exit(0)
    
    try:
        radius = int(''.join(filter(str.isdigit, user_input)))
        chatbot.user_state.update("radius", radius)
        
        print(f"\n🤖 챗봇: 반경을 {radius}m로 설정했습니다.")
        print_summary(chatbot)
    except:
        print("\n🤖 챗봇: 숫자로 입력해주세요.")
        return setup_radius(chatbot)
          
def setup_infrastructure(chatbot):
    """인프라 선호도 설정"""
    print("\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.")
    for i, infra in enumerate(INFRA_TYPES, 1):
        print(f"{i}. {infra['name']} - {infra['description']}")
    print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")
    
    user_input = input("\n🙋 사용자: ")
    
    if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
        exit(0)
    
    user_infra_preferences = {}
    try:
        # 쉼표나 공백으로 구분된 입력 처리
        if ',' in user_input:
            selections = [int(s.strip()) for s in user_input.split(',')]
        else:
            selections = [int(s.strip()) for s in user_input.split()]
        
        # 선택 검증
        if not selections or len(selections) > 3 or not all(1 <= s <= len(INFRA_TYPES) for s in selections):
            print(f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)")
            return setup_infrastructure(chatbot)
        
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
        
        # 인프라별 세부 질문
        for i, infra_type in enumerate(selected_infra_types):
            if INFRA_DETAIL_QUESTIONS.get(infra_type):
                infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type)
                print(f"\n🤖 챗봇: {infra_name}에 대한 추가 질문입니다.")
                
                for q_idx, question in enumerate(INFRA_DETAIL_QUESTIONS[infra_type]):
                    print(question)
                    answer = input("\n🙋 사용자: ")
                    if answer.lower() in ['종료', '끝', 'exit', 'quit']:
                        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
                        exit(0)
                    chatbot.user_state.update(f"infra_detail_{infra_type}_{q_idx}", answer)
        
        return user_infra_preferences
    except ValueError:
        print(f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)")
        return setup_infrastructure(chatbot)

def setup_property_features(chatbot):
    """매물 특성 설정"""
    print("\n🤖 챗봇: 이제 매물 특성에 대해 알려주세요.")
    
    for feature in PROPERTY_FEATURE_QUESTIONS:
        print(feature["question"])
        user_input = input("\n🙋 사용자: ")
        
        if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
            print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
            exit(0)
        
        chatbot.user_state.update(f"feature_{feature['code']}", user_input)
    
    chatbot.setup_complete = True
    print("\n🤖 챗봇: 설정이 완료되었습니다. 추천 매물을 찾고 있습니다...")

def display_recommendations(chatbot):
    """추천 매물 표시"""
    try:
        recommendations = chatbot.recommender.get_recommendations()
        
        # 추천 매물을 DB에 저장 시도 (기존 코드 유지)
        try:
            if hasattr(chatbot.user_state, 'save_recommendations_to_db'):
                db_save_result = chatbot.user_state.save_recommendations_to_db(recommendations)
                if db_save_result:
                    print("📊 추천 매물이 DB에 성공적으로 저장되었습니다.")
        except Exception as db_error:
            print(f"⚠️ DB 저장 중 오류 발생: {db_error}")
        
        # 결과 출력
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
        has_recommendations = bool(recommendations.get("combined") or 
                                recommendations.get("location_based") or 
                                recommendations.get("budget_based"))

        # 매물 정보 표시 (여기서 sorted_properties 정의)
        sorted_properties = []
        
        if has_recommendations:
            # 종합 추천 매물 출력
            if recommendations.get("combined"):
                # 종합 추천 매물 가져오기
                combined_properties = recommendations["combined"]
                
                # 예산 내/초과 매물 분리
                within_budget = [p for p in combined_properties if not p.get("budget_exceeded", False)]
                exceeds_budget = [p for p in combined_properties if p.get("budget_exceeded", False)]
                
                # 예산 내 매물 출력
                if within_budget:
                    print("\n🏠 [예산 내 종합 추천 매물]")
                    for i, prop in enumerate(within_budget, 1):
                        print_property(i, prop, detailed=True, user_preferences=chatbot.user_state.state)
                
                # 예산 초과 매물 출력
                if exceeds_budget:
                    print("\n⚠️ [예산 초과 종합 추천 매물]")
                    start_index = len(within_budget) + 1
                    for i, prop in enumerate(exceeds_budget, start_index):
                        print_property(i, prop, detailed=True, user_preferences=chatbot.user_state.state)
                
                # 전체 목록 저장 (관심 매물 처리용)
                sorted_properties = within_budget + exceeds_budget
            else:
                print("\n⚠️ 조건에 맞는 종합 추천 매물이 없습니다. 설정을 변경해보세요.")

            # 거주지 기반 추천 매물 출력 - 최대 3개만 표시
            if recommendations.get("location_based"):
                location_based = recommendations["location_based"][:5]  # 최대 3개까지만
                if location_based:  # 비어있지 않은 경우에만 출력
                    print("\n🏠 [거주지 기반 추천 매물]")
                    for i, prop in enumerate(location_based, 1):
                        print_property(i, prop, detailed=True, user_preferences=chatbot.user_state.state)

            # 예산 기반 추천 매물 출력 - 최대 3개만 표시
            if recommendations.get("budget_based"):
                budget_based = recommendations["budget_based"][:5]  # 최대 3개까지만
                if budget_based:  # 비어있지 않은 경우에만 출력
                    print("\n🏠 [예산 기반 추천 매물]")
                    for i, prop in enumerate(budget_based, 1):
                        print_property(i, prop, detailed=True, user_preferences=chatbot.user_state.state)
        else:
            print("\n❗ 현재 설정하신 조건에 맞는 매물을 찾지 못했습니다.")
            print("\n💡 추천 사항:")
            print("  1. 예산 범위를 넓혀보세요 (월세, 보증금 상향 조정)")
            print("  2. 검색 반경을 넓혀보세요 (현재 반경 → 더 넓은 범위)")
            print("  3. 다른 지역도 고려해보세요")

        # 관심 매물 처리
        favorite_props = {}
        if has_recommendations:
            if recommendations.get("combined"):
                favorite_props["combined"] = recommendations["combined"]
            if recommendations.get("location_based"):
                favorite_props["location_based"] = recommendations["location_based"]
            if recommendations.get("budget_based"):
                favorite_props["budget_based"] = recommendations["budget_based"]

        handle_favorites(chatbot, favorite_props if has_recommendations else {})
        
        # 종료 메시지 추가
        print("\n🤖 챗봇: 매물 추천이 완료되었습니다. 좋은 하루 되세요!")
    
    except Exception as e:
        print(f"\n❌ 추천 매물을 가져오는 중 오류가 발생했습니다: {e}")
        provide_default_properties()
        # 오류 발생시에도 종료 메시지 추가
        print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")

def handle_favorites(chatbot, properties):
    """관심 매물 처리"""
    if not properties:
        return
        
    print("\n💾 관심 매물 저장하기")
    
    # 각 섹션별 매물 목록 표시
    all_displayed_properties = []
    displayed_ids = set()  # 이미 표시된 매물 ID 또는 주소 추적
    total_index = 1
    
    # 종합 추천 매물 표시 (있는 경우)
    if "combined" in properties:
        print("\n종합 추천 매물:")
        combined_props = properties["combined"]
        for i, prop in enumerate(combined_props, total_index):
            prop_id = prop.get('id', '')
            prop_addr = prop.get('address', '')
            identifier = prop_id if prop_id else prop_addr
            
            print(f"  {i}. {prop.get('address')} ({prop.get('station')})")
            all_displayed_properties.append(prop)
            displayed_ids.add(identifier)
        total_index += len(combined_props)
    
    # 거주지 기반 추천 매물 표시 (있는 경우)
    if "location_based" in properties:
        print("\n거주지 기반 추천 매물:")
        location_props = properties["location_based"]
        shown_count = 0
        for prop in location_props:
            prop_id = prop.get('id', '')
            prop_addr = prop.get('address', '')
            identifier = prop_id if prop_id else prop_addr
            
            # 중복 체크를 제거하거나 수정하여 모든 거주지 기반 매물 표시
            # if identifier not in displayed_ids:  # 이 부분을 주석 처리하거나 제거
            print(f"  {total_index}. {prop.get('address')} ({prop.get('station')})")
            all_displayed_properties.append(prop)
            displayed_ids.add(identifier)  # 계속 추적용
            total_index += 1
            shown_count += 1
            # if shown_count >= 3:  # 최대 3개까지만 표시하려는 경우
            #     break
    
    # 예산 기반 추천 매물 표시 (있는 경우) - 동일한 수정 적용
    if "budget_based" in properties:
        print("\n예산 기반 추천 매물:")
        budget_props = properties["budget_based"]
        shown_count = 0
        for prop in budget_props:
            prop_id = prop.get('id', '')
            prop_addr = prop.get('address', '')
            identifier = prop_id if prop_id else prop_addr
            
            # 중복 체크를 제거하거나 수정
            # if identifier not in displayed_ids:  # 이 부분을 주석 처리하거나 제거
            print(f"  {total_index}. {prop.get('address')} ({prop.get('station')})")
            all_displayed_properties.append(prop)
            displayed_ids.add(identifier)  # 계속 추적용
            total_index += 1
            shown_count += 1
            # if shown_count >= 3:  # 최대 3개까지만 표시하려는 경우
            #     break
    
    print("\n추천된 매물 중 관심 있는 매물의 번호를 입력하세요 (예: 1,3 또는 1 3)")
    print("관심 없으시면 그냥 엔터키를 눌러주세요.")
    
    favorites_input = input("\n🙋 사용자: ")
    
    if not favorites_input.strip():
        # 관심 매물 없음 메시지 추가
        print("\n🤖 챗봇: 관심 매물 저장을 건너뜁니다.")
        return
        
    # 입력 파싱 (쉼표 또는 공백으로 구분)
    if ',' in favorites_input:
        favorite_numbers = [int(s.strip()) for s in favorites_input.split(',') if s.strip().isdigit()]
    else:
        favorite_numbers = [int(s.strip()) for s in favorites_input.split() if s.strip().isdigit()]
    
    # 유효한 번호만 필터링
    valid_numbers = [n for n in favorite_numbers if 1 <= n <= len(all_displayed_properties)]
    
    if valid_numbers:
        # 선택된 매물 저장
        saved_favorites = []
        for i in valid_numbers:
            if i <= len(all_displayed_properties):
                saved_favorites.append(all_displayed_properties[i-1])
        
        # 저장 결과 출력
        print(f"\n✅ {len(saved_favorites)}개의 매물을 관심 목록에 저장했습니다.")
        
        # 파일에 저장
        save_favorites_to_file(chatbot, saved_favorites)
    else:
        print("⚠️ 유효한 매물 번호가 없습니다.")
    
    # 관심 매물 보기 옵션
    view_favorites(chatbot)
    
def save_favorites_to_file(chatbot, saved_favorites):
    """관심 매물을 파일에 저장"""
    import json
    import os
    
    # 사용자별 관심 매물 폴더 생성
    favorites_dir = "favorites"
    os.makedirs(favorites_dir, exist_ok=True)
    
    # 사용자 ID 또는 기본값으로 파일명 생성
    user_id = chatbot.user_state.get("user_uuid", "default_user")
    filename = os.path.join(favorites_dir, f"{user_id}_favorites.json")
    
    # 기존 관심 매물 로드 (있으면)
    existing_favorites = []
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_favorites = json.load(f)
        except:
            pass
    
    # 새 관심 매물 추가 및 중복 제거 (ID와 주소 모두 확인)
    all_favorites = existing_favorites.copy()  # 복사본 생성으로 원본 데이터 보존
    for fav in saved_favorites:
        # ID와 주소 모두 확인하여 더 엄격한 중복 체크
        if not any((existing.get('id') == fav.get('id') or 
                   existing.get('address') == fav.get('address')) 
                   for existing in all_favorites):
            all_favorites.append(fav)
    
    # 파일에 저장
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_favorites, f, ensure_ascii=False, indent=2)
    
    print(f"💾 관심 매물이 {filename}에 저장되었습니다.")


def view_favorites(chatbot):
    """관심 매물 보기"""
    print("\n📋 관심 매물을 보시겠습니까? (y/n)")
    view_response = input("\n🙋 사용자: ").strip().lower()
    
    if view_response in ['y', 'yes', '네', '예']:
        # 관심 매물 불러오기
        import json
        import os
        
        # 사용자 ID 또는 기본값으로 파일명 생성
        user_id = chatbot.user_state.get("user_uuid", "default_user")
        filename = os.path.join("favorites", f"{user_id}_favorites.json")
        
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    favorites = json.load(f)
                
                if favorites:
                    print("\n❤️ [관심 매물 목록]")
                    print("="*60)  # 시작 구분선 추가
                    
                    for i, fav in enumerate(favorites, 1):
                        print(f"\n[매물 {i}]")
                        print_property(i, fav, detailed=True, user_preferences=chatbot.user_state.state)
                        print("-"*60)  # 매물 간 구분선 추가
                else:
                    print("\n⚠️ 저장된 관심 매물이 없습니다.")
            except Exception as e:
                print(f"\n⚠️ 관심 매물을 불러오는 중 오류가 발생했습니다: {e}")
        else:
            print("\n⚠️ 저장된 관심 매물이 없습니다.")
    
    # 종료 메시지는 한 번만 출력
    print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")

def provide_default_properties():
    """기본 매물 정보 출력"""
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

def handle_chat_conversation(chatbot):
    """챗봇과의 대화 처리"""
    print("\n🤖 챗봇: 이제 질문이 있으시면 자유롭게 물어보세요. 종료하려면 '종료'를 입력하세요.")
    
    while True:
        user_input = input("\n🙋 사용자: ")
        if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
            print("\n🤖 챗봇: 챗봇을 종료합니다. 감사합니다!")
            break
        
        # 챗봇 응답 처리
        response = chatbot.process_message(user_input)
        print(f"\n🤖 챗봇: {response}")

if __name__ == '__main__':
    # 환경 변수 MODE가 'api'인 경우 API 서버 실행, 그렇지 않으면 CLI 모드 실행
    mode = os.getenv('MODE', 'cli')
    
    if mode.lower() == 'api':
        app = create_app()
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # CLI 모드 실행
        run_cli()