from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO
import os
import uuid

# 챗봇 관련 모듈 임포트
from config import DB_CONFIG, OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME
from models.infra_types import INFRA_TYPES, INFRA_DETAIL_QUESTIONS, PROPERTY_FEATURE_QUESTIONS
from models.user_state import UserState
from services.db_service import InfraDataAccessor
from services.vector_service import VectorService
from services.llm_service import LLMProcessor
from services.recommender import RealEstateRecommender
from chatbot.chatbot import RealEstateChatbot
from utils.formatter import print_summary

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app)

# 사용자 세션 관리 딕셔너리
chatbot_sessions = {}

def get_or_create_chatbot(session_id):
    """세션 ID로 챗봇 인스턴스를 가져오거나 생성"""
    if session_id not in chatbot_sessions:
        # 서비스 초기화
        vector_service = VectorService(PINECONE_API_KEY, PINECONE_INDEX_NAME)
        data_accessor = InfraDataAccessor(DB_CONFIG)
        llm_processor = LLMProcessor(OPENAI_API_KEY)
        
        # 챗봇 인스턴스 생성
        chatbot_sessions[session_id] = {
            'chatbot': RealEstateChatbot(vector_service, data_accessor, llm_processor),
            'setup_stage': 'budget',
            'current_key': 'rent',
            'infra_preferences': {},
            'current_infra_index': 0,
            'current_question_index': 0,
            'current_feature_index': 0,
            'selected_infra_types': [],
            'retry_count': 0
        }
    
    return chatbot_sessions[session_id]

@app.route('/')
def index():
    """메인 페이지"""
    # 세션 ID 생성 또는 가져오기
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    # 챗봇 세션 초기화
    get_or_create_chatbot(session['session_id'])
    
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """채팅 API 엔드포인트"""
    data = request.json
    user_message = data.get('message', '')
    session_id = session.get('session_id')
    
    if not session_id or not user_message:
        return jsonify({'error': 'Invalid session or message'}), 400
    
    # 챗봇 세션 가져오기
    chatbot_session = get_or_create_chatbot(session_id)
    chatbot = chatbot_session['chatbot']
    setup_stage = chatbot_session['setup_stage']
    
    # 설정 완료 여부에 따라 처리
    if setup_stage == 'complete':
        # 일반 대화 모드
        response = chatbot.process_message(user_message)
    else:
        # 설정 단계별 처리
        response, next_stage, next_key = process_setup_stage(
            chatbot, 
            user_message, 
            setup_stage, 
            chatbot_session
        )
        
        # 세션 상태 업데이트
        chatbot_session['setup_stage'] = next_stage
        if next_key is not None:
            chatbot_session['current_key'] = next_key
    
    return jsonify({
        'message': response,
        'setup_stage': chatbot_session['setup_stage']
    })

def process_setup_stage(chatbot, user_message, setup_stage, session_data):
    """설정 단계별 처리 로직"""
    current_key = session_data['current_key']
    response = ""
    next_stage = setup_stage
    next_key = current_key
    
    # 특별 명령어 처리
    if user_message.lower() in ["다시", "처음부터", "초기화"]:
        # 세션 초기화
        chatbot.user_state = UserState()
        session_data['setup_stage'] = 'budget'
        session_data['current_key'] = 'rent'
        session_data['infra_preferences'] = {}
        session_data['current_infra_index'] = 0
        session_data['current_question_index'] = 0
        session_data['current_feature_index'] = 0
        session_data['selected_infra_types'] = []
        response = "설정을 초기화했습니다. 다시 시작해볼게요!\n\n현재 설정된 월세는 최대 50만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')"
        return response, 'budget', 'rent'
    
    # 예산 관련 특별 명령어
    if "예산을 올려줘" in user_message.lower() or "예산 상향" in user_message.lower():
        current_rent = chatbot.user_state.get("rent", 50)
        new_rent = int(current_rent * 1.5)  # 50% 증가
        chatbot.user_state.update("rent", new_rent)
        
        current_deposit = chatbot.user_state.get("deposit", 1000)
        new_deposit = int(current_deposit * 1.3)  # 30% 증가
        chatbot.user_state.update("deposit", new_deposit)
        
        response = f"예산을 상향 조정했습니다.\n월세: {current_rent}만원 → {new_rent}만원\n보증금: {current_deposit}만원 → {new_deposit}만원\n\n이 조건으로 다시 검색해보겠습니다."
        
        if setup_stage == 'complete':
            # 재검색 실행
            try:
                recommendations = chatbot.recommender.get_recommendations()
                result = format_recommendations(recommendations, chatbot.user_state)
                return result, 'complete', None
            except Exception as e:
                return f"검색 중 오류가 발생했습니다: {e}", 'complete', None
        return response, setup_stage, current_key
    
    # 반경 관련 특별 명령어
    if "반경을 넓혀줘" in user_message.lower() or "반경 확장" in user_message.lower():
        if chatbot.user_state.get("service") == "반경":
            current_radius = chatbot.user_state.get("radius", 500)
            new_radius = current_radius * 2  # 반경 2배 확장
            chatbot.user_state.update("radius", new_radius)
            response = f"검색 반경을 확장했습니다.\n반경: {current_radius}m → {new_radius}m\n\n이 조건으로 다시 검색해보겠습니다."
        else:
            chatbot.user_state.update("service", "반경")
            chatbot.user_state.update("radius", 1000)
            response = f"검색 방식을 반경으로 변경하고 반경을 1000m로 설정했습니다.\n\n이 조건으로 다시 검색해보겠습니다."
        
        if setup_stage == 'complete':
            # 재검색 실행
            try:
                recommendations = chatbot.recommender.get_recommendations()
                result = format_recommendations(recommendations, chatbot.user_state)
                return result, 'complete', None
            except Exception as e:
                return f"검색 중 오류가 발생했습니다: {e}", 'complete', None
        return response, setup_stage, current_key
    
    # 기본 조건 검색 명령어
    if "기본 조건" in user_message.lower():
        chatbot.user_state.update("rent", 100)
        chatbot.user_state.update("deposit", 2000)
        chatbot.user_state.update("maint", 50)
        chatbot.user_state.update("service", "반경")
        chatbot.user_state.update("radius", 1500)
        
        response = "기본 조건으로 검색 설정을 변경했습니다.\n월세: 100만원, 보증금: 2000만원, 관리비: 50만원\n검색 반경: 1500m\n\n이 조건으로 다시 검색해보겠습니다."
        
        if setup_stage == 'complete':
            # 재검색 실행
            try:
                recommendations = chatbot.recommender.get_recommendations()
                result = format_recommendations(recommendations, chatbot.user_state)
                return result, 'complete', None
            except Exception as e:
                return f"검색 중 오류가 발생했습니다: {e}", 'complete', None
        return response, setup_stage, current_key
    
    # 예산 설정 단계
    if setup_stage == "budget":
        if current_key == 'rent':
            if user_message.lower() not in ["없음", "기본"]:
                num = ''.join(filter(str.isdigit, user_message))
                if num:
                    chatbot.user_state.update("rent", int(num))
                    response = f"월세를 {num}만원으로 설정했습니다. 👍"
                else:
                    response = "월세를 기본값인 50만원으로 유지할게요."
            else:
                response = "월세를 기본값인 50만원으로 유지할게요."
            
            next_key = 'deposit'
            cur = chatbot.user_state.get(next_key)
            response += f"\n\n다음은 보증금 설정이에요. 현재 설정된 보증금은 최대 {cur}만원입니다. 조정이 필요하시다면 금액을 알려주세요. (예: 500만원, 기본, 없음)"
        
        elif current_key == 'deposit':
            if user_message.lower() not in ["없음", "기본"]:
                num = ''.join(filter(str.isdigit, user_message))
                if num:
                    chatbot.user_state.update(current_key, int(num))
                    response = f"보증금을 {num}만원으로 설정했습니다."
                else:
                    response = f"보증금을 기본값인 {chatbot.user_state.get('deposit')}만원으로 유지할게요."
            else:
                response = f"보증금을 기본값인 {chatbot.user_state.get('deposit')}만원으로 유지할게요."
            
            next_key = 'maint'
            cur = chatbot.user_state.get(next_key)
            response += f"\n\n다음은 관리비 설정이에요. 현재 설정된 관리비는 최대 {cur}만원입니다. 조정이 필요하시다면 금액을 알려주세요. (예: 10만원, 기본, 없음)"
        
        elif current_key == 'maint':
            if user_message.lower() not in ["없음", "기본"]:
                num = ''.join(filter(str.isdigit, user_message))
                if num:
                    chatbot.user_state.update(current_key, int(num))
                    response = f"관리비를 {num}만원으로 설정했습니다."
                else:
                    response = f"관리비를 기본값인 {chatbot.user_state.get('maint')}만원으로 유지할게요."
            else:
                response = f"관리비를 기본값인 {chatbot.user_state.get('maint')}만원으로 유지할게요."
            
            # 다음 단계로 이동
            response += "\n\n어떤 기준으로 매물을 추천해드릴까요?\n"
            response += "1️⃣ 소요시간 기준 - 특정 장소까지의 이동 시간으로 검색\n"
            response += "2️⃣ 반경 기준 - 특정 지점으로부터의 거리로 검색\n"
            response += "3️⃣ 상관없음 - 모든 매물 대상 검색\n\n"
            response += "원하시는 번호나 이름을 선택해주세요."
            next_stage = "location"
            next_key = 'service'
    
    # 위치 선호도 설정 단계
    elif setup_stage == "location":
        if current_key == 'service':
            service_map = {
                "1": "소요시간", "소요시간": "소요시간", "1️⃣": "소요시간",
                "2": "반경", "반경": "반경", "2️⃣": "반경",
                "3": "상관없음", "상관없음": "상관없음", "3️⃣": "상관없음"
            }
            
            service = service_map.get(user_message.lower(), "소요시간")
            chatbot.user_state.update("service", service)
            
            response = f"{service} 기준으로 설정했습니다."
            
            if service == "소요시간":
                response += "\n\n이동 방법을 선택해주세요.\n"
                response += "1️⃣ 도보 - 걸어서 이동하는 시간\n"
                response += "2️⃣ 대중교통 - 버스/지하철 등 대중교통 이용 시간\n"
                response += "3️⃣ 상관없음 - 이동 방법 무관\n"
                next_key = 'movement'
            
            elif service == "반경":
                response += "\n\n검색할 반경 거리(m)를 입력해주세요. (예: 500, 1000)"
                next_key = 'radius'
            
            else:  # 상관없음
                chatbot.user_state.update("movement", "상관없음")
                next_stage = "infra"
                response += "\n\n다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.\n"
                for i, infra in enumerate(INFRA_TYPES, 1):
                    response += f"{i}. {infra['name']} - {infra['description']}\n"
                response += "\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)"
        
        elif current_key == 'movement':
            movement_map = {
                "1": "도보", "도보": "도보", "1️⃣": "도보",
                "2": "대중교통", "대중교통": "대중교통", "2️⃣": "대중교통",
                "3": "상관없음", "상관없음": "상관없음", "3️⃣": "상관없음"
            }
            
            movement = movement_map.get(user_message.lower(), "도보")
            chatbot.user_state.update("movement", movement)
            
            response = f"이동 방법을 {movement}로 설정했습니다."
            response += "\n\n최대 몇 분 이내로 이동 가능한 매물을 찾으시나요? (예: 10, 15, 30)"
            next_key = 'time_limit'
        
        elif current_key == 'time_limit':
            try:
                time_value = int(''.join(filter(str.isdigit, user_message)))
                chatbot.user_state.update("time_limit", time_value)
                
                response = f"최대 이동 시간을 {time_value}분 이내로 설정했습니다."
                
                # 인프라 선호도 조사로 넘어감
                next_stage = "infra"
                response += "\n\n다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.\n"
                for i, infra in enumerate(INFRA_TYPES, 1):
                    response += f"{i}. {infra['name']} - {infra['description']}\n"
                response += "\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)"
                next_key = None
            except:
                response = "숫자로 입력해주세요. 예: 10, 15, 30"
        
        elif current_key == 'radius':
            try:
                radius = int(''.join(filter(str.isdigit, user_message)))
                chatbot.user_state.update("radius", radius)
                
                response = f"검색 반경을 {radius}m로 설정했습니다."
                
                # 인프라 선호도 조사로 넘어감
                next_stage = "infra"
                response += "\n\n다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.\n"
                for i, infra in enumerate(INFRA_TYPES, 1):
                    response += f"{i}. {infra['name']} - {infra['description']}\n"
                response += "\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)"
                next_key = None
            except:
                response = "숫자로 입력해주세요. 예: 500, 1000"
    
    # 인프라 선호도 설정 단계
    elif setup_stage == "infra":
        try:
            # 쉼표나 공백으로 구분된 입력 처리
            if ',' in user_message:
                selections = [int(s.strip()) for s in user_message.split(',')]
            else:
                selections = [int(s.strip()) for s in user_message.split()]
            
            # 선택 검증
            if not selections or len(selections) > 3 or not all(1 <= s <= len(INFRA_TYPES) for s in selections):
                response = f"선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)"
            else:
                # 선택한 인프라 저장 (가중치: 1순위=5, 2순위=3, 3순위=1)
                weights = [5, 3, 1]
                selected_infra_types = []
                infra_preferences = {}
                
                for i, selection in enumerate(selections):
                    if i < len(weights):  # 최대 3개까지만 처리
                        infra_type = INFRA_TYPES[selection-1]["code"]
                        infra_names = [INFRA_TYPES[selection-1]["name"]]
                        infra_preferences[infra_type] = weights[i]
                        selected_infra_types.append(infra_type)
                
                # 세션 데이터에 저장
                session_data['infra_preferences'] = infra_preferences
                session_data['selected_infra_types'] = selected_infra_types
                
                response = f"선택한 인프라를 저장했습니다: {', '.join(infra_names)}"
                
                # 인프라별 세부 질문으로 전환
                next_stage = "infra_details"
                session_data['current_infra_index'] = 0
                session_data['current_question_index'] = 0
                
                if selected_infra_types:
                    current_infra_type = selected_infra_types[0]
                    # 첫 번째 인프라의 첫 번째 질문 출력
                    if INFRA_DETAIL_QUESTIONS.get(current_infra_type) and len(INFRA_DETAIL_QUESTIONS[current_infra_type]) > 0:
                        infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == current_infra_type), current_infra_type)
                        response += f"\n\n{infra_name}에 대한 추가 질문입니다."
                        response += f"\n{INFRA_DETAIL_QUESTIONS[current_infra_type][0]}"
                    else:
                        # 질문이 없으면 다음 단계로
                        next_stage = "property_features"
                        response += "\n\n이제 매물 특성에 대해 알려주세요."
                        response += f"\n{PROPERTY_FEATURE_QUESTIONS[0]['question']}"
                        session_data['current_feature_index'] = 0
        except ValueError:
            response = f"선택이 올바르지 않습니다. 1부터 {len(INFRA_TYPES)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)"
    
    # 인프라 세부 질문 처리
    elif setup_stage == "infra_details":
        current_infra_index = session_data['current_infra_index']
        current_question_index = session_data['current_question_index']
        selected_infra_types = session_data['selected_infra_types']
        
        if current_infra_index < len(selected_infra_types):
            current_infra_type = selected_infra_types[current_infra_index]
            
            # 현재 인프라 유형의 현재 질문에 대한 응답 저장
            infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == current_infra_type), current_infra_type)
            question_list = INFRA_DETAIL_QUESTIONS.get(current_infra_type, [])
            
            if current_question_index < len(question_list):
                question = question_list[current_question_index]
                chatbot.user_state.update(f"infra_detail_{current_infra_type}_{current_question_index}", user_message)
                
                response = f"{infra_name} 질문에 대한 응답을 저장했습니다."
                
                # 다음 질문으로 이동
                current_question_index += 1
                
                # 현재 인프라 유형의 모든 질문을 완료했는지 확인
                if current_question_index >= len(question_list):
                    # 다음 인프라 유형으로 이동
                    current_infra_index += 1
                    current_question_index = 0
                    
                    # 모든 인프라 유형에 대한 질문을 완료했는지 확인
                    if current_infra_index >= len(selected_infra_types):
                        # 매물 특성 질문으로 이동
                        next_stage = "property_features"
                        response += "\n\n이제 매물 특성에 대해 알려주세요."
                        response += f"\n{PROPERTY_FEATURE_QUESTIONS[0]['question']}"
                        session_data['current_feature_index'] = 0
                    else:
                        # 다음 인프라 유형의 첫 번째 질문 출력
                        next_infra_type = selected_infra_types[current_infra_index]
                        if INFRA_DETAIL_QUESTIONS.get(next_infra_type) and len(INFRA_DETAIL_QUESTIONS[next_infra_type]) > 0:
                            next_infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == next_infra_type), next_infra_type)
                            response += f"\n\n{next_infra_name}에 대한 추가 질문입니다."
                            response += f"\n{INFRA_DETAIL_QUESTIONS[next_infra_type][0]}"
                        else:
                            # 다음 인프라에 질문이 없으면 다시 체크
                            current_infra_index += 1
                            if current_infra_index >= len(selected_infra_types):
                                next_stage = "property_features"
                                response += "\n\n이제 매물 특성에 대해 알려주세요."
                                response += f"\n{PROPERTY_FEATURE_QUESTIONS[0]['question']}"
                                session_data['current_feature_index'] = 0
                            else:
                                # 다시 다음 인프라 질문 확인
                                next_infra_type = selected_infra_types[current_infra_index]
                                if INFRA_DETAIL_QUESTIONS.get(next_infra_type) and len(INFRA_DETAIL_QUESTIONS[next_infra_type]) > 0:
                                    next_infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == next_infra_type), next_infra_type)
                                    response += f"\n\n{next_infra_name}에 대한 추가 질문입니다."
                                    response += f"\n{INFRA_DETAIL_QUESTIONS[next_infra_type][0]}"
                                else:
                                    next_stage = "property_features"
                                    response += "\n\n이제 매물 특성에 대해 알려주세요."
                                    response += f"\n{PROPERTY_FEATURE_QUESTIONS[0]['question']}"
                                    session_data['current_feature_index'] = 0
                else:
                    # 현재 인프라 유형의 다음 질문 출력
                    response += f"\n\n{INFRA_DETAIL_QUESTIONS[current_infra_type][current_question_index]}"
            else:
                # 질문이 없는 경우 다음 인프라로 이동
                current_infra_index += 1
                current_question_index = 0
                
                if current_infra_index >= len(selected_infra_types):
                    next_stage = "property_features"
                    response += "\n\n이제 매물 특성에 대해 알려주세요."
                    response += f"\n{PROPERTY_FEATURE_QUESTIONS[0]['question']}"
                    session_data['current_feature_index'] = 0
                else:
                    next_infra_type = selected_infra_types[current_infra_index]
                    if INFRA_DETAIL_QUESTIONS.get(next_infra_type) and len(INFRA_DETAIL_QUESTIONS[next_infra_type]) > 0:
                        next_infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == next_infra_type), next_infra_type)
                        response += f"\n\n{next_infra_name}에 대한 추가 질문입니다."
                        response += f"\n{INFRA_DETAIL_QUESTIONS[next_infra_type][0]}"
                    else:
                        next_stage = "property_features"
                        response += "\n\n이제 매물 특성에 대해 알려주세요."
                        response += f"\n{PROPERTY_FEATURE_QUESTIONS[0]['question']}"
                        session_data['current_feature_index'] = 0
            
            # 세션 데이터 업데이트
            session_data['current_infra_index'] = current_infra_index
            session_data['current_question_index'] = current_question_index
    
    # 매물 특성 질문 처리
    elif setup_stage == "property_features":
        current_feature_index = session_data['current_feature_index']
        
        if current_feature_index < len(PROPERTY_FEATURE_QUESTIONS):
            feature_code = PROPERTY_FEATURE_QUESTIONS[current_feature_index]["code"]
            chatbot.user_state.update(f"feature_{feature_code}", user_message)
            
            response = "응답을 저장했습니다."
            
            # 다음 질문으로 이동
            current_feature_index += 1
            if current_feature_index < len(PROPERTY_FEATURE_QUESTIONS):
                response += f"\n\n{PROPERTY_FEATURE_QUESTIONS[current_feature_index]['question']}"
            else:
                # 모든 매물 특성 질문 완료
                next_stage = "complete"
                chatbot.setup_complete = True
                chatbot.user_state.update("infra_preferences", session_data.get('infra_preferences', {}))
                
                # 추천 결과 출력
                try:
                    recommendations = chatbot.recommender.get_recommendations()
                    response = format_recommendations(recommendations, chatbot.user_state)
                    
                    # 대화 이력에 추가
                    chatbot.user_state.add_to_history("설정 완료", response)
                except Exception as e:
                    response = f"추천 매물을 가져오는 중 오류가 발생했습니다: {e}\n\n죄송합니다. 매물 검색 중 문제가 발생했습니다."
                    next_stage = "complete"  # 설정은 완료 상태로 변경
                    chatbot.setup_complete = True
            
            # 세션 데이터 업데이트
            session_data['current_feature_index'] = current_feature_index

    return response, next_stage, next_key

def format_recommendations(recommendations, user_state):
    """추천 매물 결과 포맷팅"""
    result = "설정이 완료되었습니다. 다음은 추천 매물입니다:\n\n"
    
    # 매물이 없는 경우 처리 및 자동 조건 완화
    if not recommendations["combined"]:
        result = "설정하신 조건에 맞는 매물을 찾지 못했습니다.\n\n"
        result += "조건을 자동으로 완화하여 다시 검색해보겠습니다.\n"
        
        # 조건 완화 (50% 증가)
        original_rent = user_state.get("rent", 50)
        new_rent = int(original_rent * 1.5)
        user_state.update("rent", new_rent)
        
        if user_state.get("service") == "반경":
            original_radius = user_state.get("radius", 500)
            new_radius = original_radius * 2
            user_state.update("radius", new_radius)
            result += f"- 검색 반경: {original_radius}m → {new_radius}m\n"
        
        result += f"- 월세: {original_rent}만원 → {new_rent}만원\n\n"
        
        # 재검색
        try:
            recommendations = chatbot.recommender.get_recommendations()
            
            if not recommendations["combined"]:
                # 여전히 결과가 없는 경우
                result += "조건을 완화했지만 매물을 찾지 못했습니다. 다음과 같이 조건을 변경해보세요:\n\n"
                result += "1. 예산 범위를 더 넓혀보세요 (월세, 보증금 상향 조정)\n"
                result += "2. 검색 반경을 더 넓혀보세요\n"
                result += "3. 다른 지역도 고려해보세요\n\n"
                result += "조건을 변경하시겠어요? '예산을 올려줘', '반경을 넓혀줘', '기본 조건으로 검색해줘' 등으로 요청해주세요."
                return result
        except Exception as e:
            return f"추천 매물을 가져오는 중 오류가 발생했습니다: {e}\n\n죄송합니다. 매물 검색 중 문제가 발생했습니다."
    
    # 유효한 매물만 필터링 (주소 정보가 있는 매물)
    valid_combined = [prop for prop in recommendations["combined"] 
                     if prop.get('address') and prop.get('address') != '주소 정보 없음']
    
    if valid_combined:
        result += "**🏠 추천 매물 (위치+예산+인프라)**\n\n"
        for i, prop in enumerate(valid_combined, 1):
            # 소수점 값들을 정수로 변환
            rent = int(float(prop.get('rent', 0))) if prop.get('rent') is not None else '?'
            deposit = int(float(prop.get('deposit', 0))) if prop.get('deposit') is not None else '?'
            maint = int(float(prop.get('maint', 0))) if prop.get('maint') is not None else '?'
            infra_score = round(float(prop.get('infra_score', 0)), 1)
            
            # 시간 정보에서 소수점 제거
            time_info = prop.get('time_info', '')
            if time_info:
                time_info = time_info.replace('.0분', '분')
            
            # 방 타입 정보 추가
            room_type = prop.get('room_type', '')
            room_info = f" {room_type}" if room_type else ""
            
            result += f"{i}. {prop['address']} ({prop['station']}){room_info}\n"
            result += f"   월세: {rent}만원, 보증금: {deposit}만원, 관리비: {maint}만원\n"
            
            # 추가 정보 (층수, 면적, 방향 등)
            floor = prop.get('floor', '정보 없음')
            area = f"{int(float(prop.get('area', 0)))}㎡" if prop.get('area') is not None else '정보 없음'
            direction = prop.get('direction', '정보 없음')
            heating = prop.get('heating_type', '정보 없음')
            parking = '가능' if prop.get('parking') else '불가능'
            elevator = '있음' if prop.get('elevator') else '없음'
            
            result += f"   층수: {floor}, 면적: {area}, 방향: {direction}\n"
            result += f"   난방: {heating}, 주차: {parking}, 엘리베이터: {elevator}\n"
            result += f"   {time_info}, 인프라 점수: {infra_score:.1f}\n"
            
            # 인프라 세부 정보 추가
            if prop.get("infra_details"):
                result += "   인프라 세부 정보:\n"
                for infra_type, detail in prop["infra_details"].items():
                    if detail.get("score", 0) > 0:
                        infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type)
                        distance = int(detail.get('distance', 0))
                        result += f"   - {infra_name}: {detail['nearest']} (거리: {distance}m)\n"
            
            result += "\n"
    else:
        # 유효한 매물이 없는 경우, 필터링 전 매물 사용
        result += "**🏠 추천 매물 (위치+예산+인프라)**\n\n"
        for i, prop in enumerate(recommendations["combined"][:3], 1):
            # 소수점 값들을 정수로 변환
            rent = int(float(prop.get('rent', 0))) if prop.get('rent') is not None else '?'
            deposit = int(float(prop.get('deposit', 0))) if prop.get('deposit') is not None else '?'
            maint = int(float(prop.get('maint', 0))) if prop.get('maint') is not None else '?'
            infra_score = round(float(prop.get('infra_score', 0)), 1)
            
            # 시간 정보에서 소수점 제거
            time_info = prop.get('time_info', '')
            if time_info:
                time_info = time_info.replace('.0분', '분')
            
            # 방 타입 정보 추가
            room_type = prop.get('room_type', '')
            room_info = f" {room_type}" if room_type else ""
            
            result += f"{i}. {prop.get('address', '주소 정보 없음')} ({prop.get('station', '역 정보 없음')}){room_info}\n"
            result += f"   월세: {rent}만원, 보증금: {deposit}만원, 관리비: {maint}만원\n"
            
            # 추가 정보 (층수, 면적, 방향 등)
            floor = prop.get('floor', '정보 없음')
            area = f"{int(float(prop.get('area', 0)))}㎡" if prop.get('area') is not None else '정보 없음'
            direction = prop.get('direction', '정보 없음')
            heating = prop.get('heating_type', '정보 없음')
            parking = '가능' if prop.get('parking') else '불가능'
            elevator = '있음' if prop.get('elevator') else '없음'
            
            result += f"   층수: {floor}, 면적: {area}, 방향: {direction}\n"
            result += f"   난방: {heating}, 주차: {parking}, 엘리베이터: {elevator}\n"
            result += f"   {time_info}, 인프라 점수: {infra_score:.1f}\n"
            
            # 인프라 세부 정보 추가
            if prop.get("infra_details"):
                result += "   인프라 세부 정보:\n"
                for infra_type, detail in prop["infra_details"].items():
                    if detail.get("score", 0) > 0:
                        infra_name = next((x["name"] for x in INFRA_TYPES if x["code"] == infra_type), infra_type)
                        distance = int(detail.get('distance', 0))
                        result += f"   - {infra_name}: {detail['nearest']} (거리: {distance}m)\n"
            
            result += "\n"
    
    result += "추천 매물에 대해 더 알고 싶으신 내용이 있으신가요? (예: '1번 매물에 대해 자세히 알려줘', '예산을 올려줘', '반경을 넓혀줘')"
    return result

@socketio.on('connect')
def handle_connect():
    """소켓 연결 이벤트 처리"""
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """소켓 연결 해제 이벤트 처리"""
    print(f"Client disconnected: {request.sid}")
    # 연결이 끊겼을 때 세션 정리 (선택 사항)
    session_id = session.get('session_id')
    if session_id and session_id in chatbot_sessions:
        del chatbot_sessions[session_id]

if __name__ == '__main__':
    socketio.run(app, debug=True)