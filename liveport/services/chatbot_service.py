import time
import json
import os
import copy
import psycopg2
from psycopg2.extras import Json
from openai import OpenAI
from pinecone import Pinecone
from liveport.config import Config  
from liveport.models.user_model import UserState
from liveport.services.recommender_service import RealEstateRecommender 

# 클라이언트 초기화
client = OpenAI(api_key=Config.OPENAI_API_KEY)
pc = Pinecone(api_key=Config.PINECONE_API_KEY)
index = pc.Index(Config.PINECONE_INDEX_NAME)

class LLMProcessor:
    def __init__(self, client):
        self.client = client
    
    def generate_response(self, user_message, context, chat_history):
        """LLM을 사용하여 응답 생성"""
        # 대화 이력 포맷팅
        history_text = ""
        for entry in chat_history:
            history_text += f"사용자: {entry['user']}\n봇: {entry['bot']}\n\n"
        
        # 컨텍스트 포맷팅
        context_text = self._format_context(context)
        
        # LLM 프롬프트 구성
        prompt = f"""당신은 부동산 매물 추천 AI 챗봇입니다. 사용자의 위치, 예산, 이동 방식, 인프라 선호도, 매물 특성 등을 고려하여 최적의 매물을 추천해주세요.

대화 이력:
{history_text}

추천 매물 정보:
{context_text}

사용자 메시지: {user_message}

친절하고 도움이 되는 응답을 제공해주세요. 사용자가 특정 매물에 관심을 보이면 더 자세한 정보를 제공하고, 
추가 질문이 있으면 답변해주세요. 매물이 없는 경우에도 항상 추천 매물을 보여주세요.
"""

        try:
            # LLM 호출
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 응답 생성 오류: {e}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다. 다시 시도해주세요."
    
    def _format_context(self, context):
        """컨텍스트 포맷팅"""
        context_text = ""
        
        # 각 타입별 추천 매물 정보 포맷팅
        for rec_type in ["location_based", "budget_based", "combined"]:
            if not context.get(rec_type):
                continue
                
            type_name = {
                "location_based": "위치 기반",
                "budget_based": "예산 기반",
                "combined": "종합"
            }.get(rec_type)
            
            context_text += f"\n{type_name} 추천 매물:\n"
            for i, prop in enumerate(context[rec_type], 1):
                infra_score = prop.get("infra_score", 0)
                context_text += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                context_text += f"   층수: {prop['floor']}, 난방: {prop['heating_type']}, 주차: {'가능' if prop['parking'] else '불가능'}\n"
                context_text += f"   시설: {prop.get('facilities', '')}\n"
                
                # 인프라 세부 정보 추가
                if prop.get("infra_details"):
                    context_text += "   인프라 세부 정보:\n"
                    for infra_type, detail in prop["infra_details"].items():
                        if detail.get("score", 0) > 0:
                            context_text += f"     - {infra_type}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
        
        # 추천 매물이 없는 경우, 대체 매물 검색 (조건 완화)
        if not context_text:
            return "검색 조건에 맞는 매물을 찾지 못했습니다. 다른 조건으로 다시 검색해보세요."

class RealEstateChatbot:
    def __init__(self, user_uuid=None):
        self.user_uuid = user_uuid
        self.user_state = UserState(user_uuid)
        self.recommender = RealEstateRecommender(index, self.user_state)
        self.llm = LLMProcessor(client)
        self.setup_complete = False
        
        # 환경 변수에서 데이터베이스 연결 정보 가져오기
        self.db_config = {
            'host': os.getenv("POSTGRES_HOST", "zipup-db.cnkoy8gkiz2v.ap-southeast-2.rds.amazonaws.com"),
            'database': os.getenv("POSTGRES_DB", "postgres"),
            'user': os.getenv("POSTGRES_USER", "teammate"),
            'password': os.getenv("POSTGRES_PASSWORD", "teampass123"),
            'port': int(os.getenv("POSTGRES_PORT", "5432"))
        }
        
        # 대화 상태 테이블 확인
        self._ensure_state_table_exists()
        
        # 대화 상태 로드
        self.conversation_state = self._load_conversation_state()
    
    def _get_db_connection(self):
        """데이터베이스 연결 얻기"""
        return psycopg2.connect(**self.db_config)
    
    def _ensure_state_table_exists(self):
        """대화 상태 테이블이 존재하는지 확인하고 없으면 생성"""
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            
            # 테이블 존재 여부 확인 및 생성
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_conversation_states (
                    user_uuid VARCHAR(255) PRIMARY KEY,
                    state_data JSONB NOT NULL,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            cur.close()
        except Exception as e:
            print(f"테이블 생성 오류: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def _load_conversation_state(self):
        """사용자의 대화 상태를 데이터베이스에서 로드"""
        conn = None
        try:
            if not self.user_uuid:
                return self._get_default_state()
            
            conn = self._get_db_connection()
            cur = conn.cursor()
            
            # 사용자 대화 상태 조회
            cur.execute(
                "SELECT state_data FROM user_conversation_states WHERE user_uuid = %s",
                (self.user_uuid,)
            )
            
            result = cur.fetchone()
            cur.close()
            
            if result:
                print(f"사용자 {self.user_uuid}의 저장된 대화 상태 로드 성공")
                return result[0]  # PostgreSQL JSONB 타입은 자동으로 Python 딕셔너리로 변환됨
            
            # 상태가 없는 경우 기본 상태 반환
            return self._get_default_state()
            
        except Exception as e:
            print(f"대화 상태 로드 오류: {e}")
            return self._get_default_state()
        finally:
            if conn:
                conn.close()
    
    def _get_default_state(self):
        """기본 대화 상태 반환"""
        return {
            "step": 1,
            "data": {
                "monthly": "60",
                "budget": "1000",
                "maintenance_fee": "15"
            }
        }
    
    def _save_conversation_state(self):
        """사용자의 대화 상태를 데이터베이스에 저장"""
        if not self.user_uuid:
            print("사용자 ID가 없어 대화 상태를 저장할 수 없습니다.")
            return
            
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            
            # UPSERT 쿼리
            cur.execute("""
                INSERT INTO user_conversation_states (user_uuid, state_data, updated_at)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_uuid) 
                DO UPDATE SET 
                    state_data = %s,
                    updated_at = CURRENT_TIMESTAMP
            """, (self.user_uuid, Json(self.conversation_state), Json(self.conversation_state)))
            
            conn.commit()
            cur.close()
            print(f"사용자 {self.user_uuid}의 대화 상태 저장 성공: {self.conversation_state}")
            
        except Exception as e:
            print(f"대화 상태 저장 오류: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def _extract_numbers(self, text):
        """텍스트에서 숫자만 추출"""
        import re
        match = re.search(r'\d+', text)
        return match.group(0) if match else None
    
    def _parse_infra_selection(self, text):
        """인프라 선택 텍스트 파싱 (개선 버전)"""
        import re
        
        # 기본 숫자 파싱
        numbers = re.findall(r'\d+', text)
        
        # 숫자가 없는 경우, 키워드 기반 파싱 시도
        if not numbers:
            lower_text = text.lower()
            
            # 키워드 매핑
            keyword_mapping = {
                '지하철': '1', '지하철역': '1', '역': '1',
                '버스': '2', '버스정류장': '2',
                '마트': '3', '대형마트': '3',
                '백화점': '4',
                '편의점': '5',
                '주민센터': '6',
                '다이소': '7',
                '카페': '8',
                '공원': '9',
                '우체국': '10',
                '헬스': '11', '헬스장': '11', '운동': '11',
                '병원': '12',
                '약국': '13',
                '영화관': '14', '영화': '14',
                'pc방': '15', '피시방': '15',
                '노래방': '16',
                '파출소': '17', '경찰서': '17'
            }
            
            found_numbers = []
            for keyword, number in keyword_mapping.items():
                if keyword in lower_text:
                    found_numbers.append(number)
            
            # 중복 제거하고 반환
            numbers = list(set(found_numbers))
        
        # 최소 1개는 선택되도록
        if not numbers:
            numbers = ['1']  # 지하철역을 기본값으로 설정
        
        # 최대 3개까지 제한
        if len(numbers) > 3:
            numbers = numbers[:3]
            
        return numbers
    
    def process_message(self, user_message):
        """사용자 메시지 처리"""
        # 현재 대화 상태 확인 (디버그용)
        print(f"[DEBUG] 메시지 처리 시작 - 사용자: {self.user_uuid}")
        print(f"[DEBUG] 현재 대화 단계: {self.conversation_state.get('step', 1)}")
        print(f"[DEBUG] 사용자 메시지: {user_message}")
        print(f"[DEBUG] 현재 대화 상태: {self.conversation_state}")
        
        # 현재 대화 단계 확인
        current_step = self.conversation_state.get("step", 1)
        data = self.conversation_state.get("data", {})
        
        # 단계별 처리 로직
        if current_step == 1:  # 월세 질문
            # 사용자 입력 처리
            if user_message.lower() == '없음':
                monthly = data.get("monthly", "60")
            else:
                # 사용자 입력에서 숫자 추출
                extracted = self._extract_numbers(user_message)
                monthly = extracted if extracted else data.get("monthly", "60")
            
            # 상태 업데이트
            data["monthly"] = monthly
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 2  # 다음 단계(보증금 질문)로 이동
            
            # 응답 생성
            budget = data.get("budget", "1000")
            maintenance_fee = data.get("maintenance_fee", "15")
            response = f"{monthly}만원으로 설정했습니다.\n\n## 현재까지의 설정 요약\n\n- 월세: {monthly}만원\n- 보증금: {budget}만원\n- 관리비: {maintenance_fee}만원\n\n현재 설정하신 보증금은 최대 {budget}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')"
            
        elif current_step == 2:  # 보증금 질문
            # 보증금 입력 처리
            if user_message.lower() == '없음':
                budget = data.get("budget", "1000")
            else:
                # 사용자 입력에서 숫자 추출
                extracted = self._extract_numbers(user_message)
                budget = extracted if extracted else data.get("budget", "1000")
            
            # 상태 업데이트
            data["budget"] = budget
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 3  # 다음 단계(관리비 질문)로 이동
            
            # 응답 생성
            monthly = data.get("monthly", "60")
            maintenance_fee = data.get("maintenance_fee", "15")
            response = f"{budget}만원으로 설정했습니다.\n\n## 현재까지의 설정 요약\n\n- 월세: {monthly}만원\n- 보증금: {budget}만원\n- 관리비: {maintenance_fee}만원\n\n현재 설정하신 관리비는 최대 {maintenance_fee}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')"
        
        elif current_step == 3:  # 관리비 질문
            # 관리비 입력 처리
            if user_message.lower() == '없음':
                maintenance_fee = data.get("maintenance_fee", "15")
            else:
                # 사용자 입력에서 숫자 추출
                extracted = self._extract_numbers(user_message)
                maintenance_fee = extracted if extracted else data.get("maintenance_fee", "15")
            
            # 상태 업데이트
            data["maintenance_fee"] = maintenance_fee
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 4  # 다음 단계(추천 기준 질문)로 이동
            
            # 응답 생성
            monthly = data.get("monthly", "60")
            budget = data.get("budget", "1000")
            response = f"{maintenance_fee}만원으로 설정했습니다.\n\n## 현재까지의 설정 요약\n\n- 월세: {monthly}만원\n- 보증금: {budget}만원\n- 관리비: {maintenance_fee}만원\n\n어떤 기준으로 추천할까요?\n\n1. 소요시간 기준\n2. 반경 기준 (m 단위)\n3. 상관없음"
        
        elif current_step == 4:  # 추천 기준 선택
            # 추천 기준 입력 처리 - 개선된 한글 인식
            criteria = "3"  # 기본값은 상관없음
            
            # 텍스트 기반 분석 추가
            lower_msg = user_message.lower()
            if "1" in lower_msg or "소요" in lower_msg or "시간" in lower_msg:
                criteria = "1"
            elif "2" in lower_msg or "반경" in lower_msg:
                criteria = "2"
            elif "3" in lower_msg or "상관" in lower_msg or "없" in lower_msg:
                criteria = "3"
            
            data["criteria"] = criteria
            self.conversation_state["data"] = data
            
            # 기준에 따라 다음 단계 결정
            if criteria == "1":
                # 소요시간 기준을 선택한 경우
                self.conversation_state["step"] = 4.1  # 이동 방법 선택 단계로 이동
                response = f"소요시간 기준으로 설정했습니다.\n\n## 현재까지의 설정 요약\n\n- 월세: {data.get('monthly')}만원\n- 보증금: {data.get('budget')}만원\n- 관리비: {data.get('maintenance_fee')}만원\n- 추천 기준: 소요시간\n\n이동 방법을 선택해주세요:\n\n1. 도보\n2. 대중교통\n3. 상관없음"
            elif criteria == "2":
                # 반경 기준을 선택한 경우
                self.conversation_state["step"] = 5  # 반경 입력 단계로 이동
                response = f"반경 기준으로 설정했습니다.\n\n## 현재까지의 설정 요약\n\n- 월세: {data.get('monthly')}만원\n- 보증금: {data.get('budget')}만원\n- 관리비: {data.get('maintenance_fee')}만원\n- 추천 기준: 반경\n\n반경(m)을 입력하세요"
            else:
                # 상관없음 선택
                self.conversation_state["step"] = 6  # 인프라 선택 단계로 이동
                response = f"상관없음 기준으로 설정했습니다.\n\n## 현재까지의 설정 요약\n\n- 월세: {data.get('monthly')}만원\n- 보증금: {data.get('budget')}만원\n- 관리비: {data.get('maintenance_fee')}만원\n- 추천 기준: 상관없음\n\n다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.\n\n1. 지하철역 - 대중교통 접근성\n2. 버스정류장 - 버스 노선 접근성\n3. 대형마트 - 쇼핑 및 생필품 구매\n4. 백화점 - 쇼핑 및 편의시설\n5. 편의점 - 생필품 및 간편식품\n6. 주민센터 - 행정 및 복지 서비스\n7. 다이소 - 생활용품 및 잡화\n8. 카페 - 휴식 및 업무 공간\n9. 공원 - 여가 및 산책 공간\n10. 우체국 - 우편 및 행정 서비스\n11. 헬스장 - 건강 관리 및 운동 시설\n12. 병원 - 의료 서비스\n13. 약국 - 의약품 구매\n14. 영화관 - 문화 및 엔터테인먼트\n15. PC방 - 게임 및 인터넷\n16. 노래방 - 엔터테인먼트\n17. 파출소/경찰서 - 치안 및 안전\n\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)"
        
        # 새로 추가된 단계: 이동 방법 선택
        elif current_step == 4.1:  # 이동 방법 선택
            movement = "도보"  # 기본값
            
            # 사용자 입력 처리
            lower_msg = user_message.lower()
            if "1" in lower_msg or "도보" in lower_msg or "걷" in lower_msg:
                movement = "도보"
            elif "2" in lower_msg or "대중" in lower_msg or "교통" in lower_msg or "버스" in lower_msg or "지하철" in lower_msg:
                movement = "대중교통"
            elif "3" in lower_msg or "상관" in lower_msg or "없" in lower_msg:
                movement = "상관없음"
            
            # 상태 업데이트
            data["movement"] = movement
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 4.2  # 소요시간 입력 단계로 이동
            
            # 응답 생성
            response = f"이동 방법을 '{movement}'(으)로 설정했습니다.\n\n## 현재까지의 설정 요약\n\n- 월세: {data.get('monthly')}만원\n- 보증금: {data.get('budget')}만원\n- 관리비: {data.get('maintenance_fee')}만원\n- 추천 기준: 소요시간\n- 이동 방법: {movement}\n\n최대 몇 분 이내를 원하시나요? (숫자만 입력해주세요)"
        
        # 새로 추가된 단계: 소요시간 입력
        elif current_step == 4.2:  # 소요시간 입력
            # 소요시간 입력 처리
            time_limit = self._extract_numbers(user_message) or "30"  # 기본값
            
            # 상태 업데이트
            data["time_limit"] = time_limit
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 6  # 인프라 선택 단계로 이동
            
            movement = data.get("movement", "도보")
            
            # 응답 생성
            response = f"소요시간을 {time_limit}분 이내로 설정했습니다.\n\n## 현재까지의 설정 요약\n\n- 월세: {data.get('monthly')}만원\n- 보증금: {data.get('budget')}만원\n- 관리비: {data.get('maintenance_fee')}만원\n- 추천 기준: 소요시간\n- 이동 방법: {movement}\n- 소요시간: {time_limit}분 이내\n\n다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.\n\n1. 지하철역 - 대중교통 접근성\n2. 버스정류장 - 버스 노선 접근성\n3. 대형마트 - 쇼핑 및 생필품 구매\n4. 백화점 - 쇼핑 및 편의시설\n5. 편의점 - 생필품 및 간편식품\n6. 주민센터 - 행정 및 복지 서비스\n7. 다이소 - 생활용품 및 잡화\n8. 카페 - 휴식 및 업무 공간\n9. 공원 - 여가 및 산책 공간\n10. 우체국 - 우편 및 행정 서비스\n11. 헬스장 - 건강 관리 및 운동 시설\n12. 병원 - 의료 서비스\n13. 약국 - 의약품 구매\n14. 영화관 - 문화 및 엔터테인먼트\n15. PC방 - 게임 및 인터넷\n16. 노래방 - 엔터테인먼트\n17. 파출소/경찰서 - 치안 및 안전\n\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)"
        
        elif current_step == 5:  # 반경 입력
            # 반경 입력 처리
            extracted = self._extract_numbers(user_message)
            radius = extracted if extracted else "2000"  # 기본값
            
            # 상태 업데이트
            data["radius"] = radius
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 6  # 인프라 선택 단계로 이동
            
            # 응답 생성
            response = f"반경을 {radius}m로 설정했습니다.\n\n## 현재까지의 설정 요약\n\n- 월세: {data.get('monthly')}만원\n- 보증금: {data.get('budget')}만원\n- 관리비: {data.get('maintenance_fee')}만원\n- 추천 기준: 반경\n- 반경: {radius}m\n\n다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.\n\n1. 지하철역 - 대중교통 접근성\n2. 버스정류장 - 버스 노선 접근성\n3. 대형마트 - 쇼핑 및 생필품 구매\n4. 백화점 - 쇼핑 및 편의시설\n5. 편의점 - 생필품 및 간편식품\n6. 주민센터 - 행정 및 복지 서비스\n7. 다이소 - 생활용품 및 잡화\n8. 카페 - 휴식 및 업무 공간\n9. 공원 - 여가 및 산책 공간\n10. 우체국 - 우편 및 행정 서비스\n11. 헬스장 - 건강 관리 및 운동 시설\n12. 병원 - 의료 서비스\n13. 약국 - 의약품 구매\n14. 영화관 - 문화 및 엔터테인먼트\n15. PC방 - 게임 및 인터넷\n16. 노래방 - 엔터테인먼트\n17. 파출소/경찰서 - 치안 및 안전\n\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)"


        elif current_step == 6:  # 인프라 선택
            # 인프라 선택 처리 (개선된 버전)
            infra_numbers = self._parse_infra_selection(user_message)
            
            # 인프라 이름 매핑
            infra_names = {
                "1": "지하철역",
                "2": "버스정류장",
                "3": "대형마트",
                "4": "백화점",
                "5": "편의점",
                "6": "주민센터",
                "7": "다이소",
                "8": "카페",
                "9": "공원",
                "10": "우체국",
                "11": "헬스장",
                "12": "병원",
                "13": "약국",
                "14": "영화관",
                "15": "PC방",
                "16": "노래방",
                "17": "파출소/경찰서"
            }
            
            # 인프라 코드 매핑
            infra_codes = {
                "1": "traffic_subway",
                "2": "traffic_bus",
                "3": "life_mart",
                "4": "life_department_store",
                "5": "life_convenience_store",
                "6": "life_community_center",
                "7": "life_daiso",
                "8": "life_cafe",
                "9": "life_park",
                "10": "life_post_office",
                "11": "life_healthjang",
                "12": "health_hospital",
                "13": "health_pharmacy",
                "14": "play_cinema",
                "15": "play_pc_cafe",
                "16": "play_karaoke",
                "17": "safety_police_station"
            }
            
            # 선택한 인프라 이름 가져오기
            selected_infra_names = [infra_names.get(num, f"인프라 {num}") for num in infra_numbers]
            
            # 인프라 선호도 설정 - 가중치 적용 (1순위=5, 2순위=3, 3순위=1)
            weights = [5, 3, 1]
            infra_preferences = {}
            for i, num in enumerate(infra_numbers):
                if i < len(weights) and num in infra_codes:
                    infra_preferences[infra_codes[num]] = weights[i]
            
            # 상태 업데이트
            data["infrastructure"] = infra_numbers
            data["infra_names"] = selected_infra_names
            data["infra_preferences"] = infra_preferences  # 인프라 선호도 저장!
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 7  # 첫 번째 인프라 중요도 질문으로 이동
            data["current_infra_idx"] = 0  # 첫 번째 인프라 인덱스
            
            # 응답 생성
            response_parts = [
                "선택한 인프라를 저장했습니다.",
                "",
                "## 현재까지의 설정 요약",
                "",
                f"- 월세: {data.get('monthly')}만원",
                f"- 보증금: {data.get('budget')}만원",
                f"- 관리비: {data.get('maintenance_fee')}만원"
            ]
            
            if data.get("criteria") == "2":
                response_parts.append(f"- 추천 기준: 반경")
                response_parts.append(f"- 반경: {data.get('radius')}m")
            elif data.get("criteria") == "1":
                response_parts.append(f"- 추천 기준: 소요시간")
                response_parts.append(f"- 이동 방법: {data.get('movement', '도보')}")
                response_parts.append(f"- 소요시간: {data.get('time_limit', '30')}분 이내")
            else:
                response_parts.append(f"- 추천 기준: 상관없음")
            
            response_parts.append(f"- 선택한 인프라: {', '.join(selected_infra_names)}")
            response_parts.append("")
            
            # 첫 번째 인프라에 대한 질문
            first_infra = selected_infra_names[0] if selected_infra_names else "지하철역"
            response_parts.append(f"{first_infra}에 대한 질문입니다.")
            response_parts.append("이 시설이 얼마나 중요한가요? (1: 별로 중요하지 않음 ~ 5: 매우 중요함)")
            
            response = "\n".join(response_parts)
        
        elif current_step == 7:  # 인프라 중요도 질문
            # 현재 처리 중인 인프라 인덱스와 이름
            current_idx = data.get("current_infra_idx", 0)
            infra_names = data.get("infra_names", [])
            current_infra = infra_names[current_idx] if current_idx < len(infra_names) else "지하철역"
            
            # 인프라 중요도 저장
            importance = self._extract_numbers(user_message) or "3"
            
            # 인프라 세부 정보 초기화
            if "infra_details" not in data:
                data["infra_details"] = {}
            
            # 현재 인프라의 세부 정보 초기화
            if current_infra not in data["infra_details"]:
                data["infra_details"][current_infra] = {}
            
            # 중요도 저장
            data["infra_details"][current_infra]["importance"] = importance
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 8  # 다음 단계(도보 시간 질문)로 이동
            
            # 응답 생성
            response = f"이 시설까지 도보 몇 분 이내가 좋으신가요? (숫자만 입력해주세요)"
        
        elif current_step == 8:  # 도보 시간 질문
            # 현재 처리 중인 인프라 인덱스와 이름
            current_idx = data.get("current_infra_idx", 0)
            infra_names = data.get("infra_names", [])
            current_infra = infra_names[current_idx] if current_idx < len(infra_names) else "지하철역"
            
            # 도보 시간 저장
            walk_time = self._extract_numbers(user_message) or "10"
            data["infra_details"][current_infra]["walk_time"] = walk_time
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 9  # 다음 단계(이용 빈도 질문)로 이동
            
            # 응답 생성
            response = f"이 시설을 얼마나 자주 이용하실 계획인가요? (1: 거의 이용 안함 ~ 5: 거의 매일)"
        
        elif current_step == 9:  # 이용 빈도 질문
            # 현재 처리 중인 인프라 인덱스와 이름
            current_idx = data.get("current_infra_idx", 0)
            infra_names = data.get("infra_names", [])
            current_infra = infra_names[current_idx] if current_idx < len(infra_names) else "지하철역"
            
            print(f"[DEBUG] 이용 빈도 처리 - 현재 인프라: {current_infra}, 인덱스: {current_idx}")
            
            # 이용 빈도 저장
            frequency = self._extract_numbers(user_message) or "3"
            
            # 인프라 세부 정보 초기화 확인
            if "infra_details" not in data:
                data["infra_details"] = {}
            
            # 현재 인프라의 세부 정보 초기화 확인
            if current_infra not in data["infra_details"]:
                data["infra_details"][current_infra] = {}
            
            # 이용 빈도 저장
            data["infra_details"][current_infra]["frequency"] = frequency
            
            print(f"[DEBUG] 저장된 이용 빈도: {frequency}, 인프라: {current_infra}")
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            
            # 중요도가 높은 경우(4-5점) 추가 질문
            importance = data["infra_details"][current_infra].get("importance", "3")
            
            print(f"[DEBUG] 중요도 체크: {importance}")
            
            # 중요도가 높은 경우 추가 질문, 아니면 다음 단계로
            if importance in ["4", "5"]:
                self.conversation_state["step"] = 10  # 인프라 추가 질문으로 이동
                print(f"[DEBUG] 높은 중요도, 단계 10으로 이동")
                
                # 인프라 코드 가져오기
                infra_code = self._get_infra_code(current_infra)
                
                # 인프라별 추가 질문
                if infra_code and infra_code in Config.INFRA_DETAIL_QUESTIONS_V2["specific_questions"]:
                    # Config에서 질문 가져오기
                    question_dict = Config.INFRA_DETAIL_QUESTIONS_V2["specific_questions"][infra_code]
                    question_key = list(question_dict.keys())[0]  # 첫 번째 질문 키
                    question = question_dict[question_key]
                    
                    response = f"{current_infra}이(가) 중요하시군요! 조금 더 자세히 알려주세요.\n{question}"
                    print(f"[DEBUG] 추가 질문 생성: {response}")
                else:
                    # 다음 인프라로 이동 또는 매물 특성 질문으로 이동
                    print(f"[DEBUG] 인프라 코드 없음 또는 추가 질문 없음, 다음 단계로 이동")
                    response = self._process_after_infra_questions(current_idx, infra_names)
            else:
                # 다음 인프라로 이동 또는 매물 특성 질문으로 이동
                print(f"[DEBUG] 낮은 중요도, 다음 단계로 이동")
                response = self._process_after_infra_questions(current_idx, infra_names)
            
            # 대화 상태 즉시 저장
            self._save_conversation_state()
            print(f"[DEBUG] 단계 9 처리 완료, 다음 단계: {self.conversation_state.get('step')}")
        
        elif current_step == 10:  # 인프라 추가 질문
            # 현재 처리 중인 인프라 인덱스와 이름
            current_idx = data.get("current_infra_idx", 0)
            infra_names = data.get("infra_names", [])
            current_infra = infra_names[current_idx] if current_idx < len(infra_names) else "지하철역"
            
            # 추가 질문 응답 저장
            data["infra_details"][current_infra]["additional_info"] = user_message
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            
            # 다음 인프라로 이동 또는 매물 특성 질문으로 이동
            response = self._process_after_infra_questions(current_idx, infra_names)
        
        elif current_step == 11:  # 매물 특성 질문 - 주거 타입
            # 주거 타입 저장
            if "property_preferences" not in data:
                data["property_preferences"] = {}
                
            # 주거 타입 처리 - 키워드 기반 분석
            lower_msg = user_message.lower()
            if "원룸" in lower_msg:
                housing_type = "원룸"
            elif "투룸" in lower_msg:
                housing_type = "투룸"
            elif "쓰리룸" in lower_msg or "쓰리" in lower_msg or "3룸" in lower_msg:
                housing_type = "쓰리룸"
            elif "오피스텔" in lower_msg or "오피" in lower_msg:
                housing_type = "오피스텔"
            elif "상관" in lower_msg or "없" in lower_msg:
                housing_type = "상관없음"
            else:
                housing_type = user_message  # 그대로 저장
                
            data["property_preferences"]["housing_type"] = housing_type
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 12  # 다음 단계(층수 질문)로 이동
            
            # 응답 생성
            response = f"선호하시는 층수가 있으신가요? (예: 저층(1-3층), 중층(4-7층), 고층(8층 이상), 반지하 제외, 상관없음)"
        
        elif current_step == 12:  # 매물 특성 질문 - 층수
            # 층수 선호도 처리 - 키워드 기반 분석
            lower_msg = user_message.lower()
            if "저층" in lower_msg or "1층" in lower_msg or "2층" in lower_msg or "3층" in lower_msg:
                floor = "저층(1-3층)"
            elif "중층" in lower_msg or "4층" in lower_msg or "5층" in lower_msg or "6층" in lower_msg or "7층" in lower_msg:
                floor = "중층(4-7층)"
            elif "고층" in lower_msg or "8층" in lower_msg or "9층" in lower_msg or "10층" in lower_msg:
                floor = "고층(8층 이상)"
            elif "반지하" in lower_msg and "제외" in lower_msg:
                floor = "반지하 제외"
            elif "2층" in lower_msg and "이상" in lower_msg:
                floor = "2층 이상"
            elif "상관" in lower_msg or "없" in lower_msg:
                floor = "상관없음"
            else:
                floor = user_message  # 그대로 저장
                
            # 층수 저장
            data["property_preferences"]["floor"] = floor
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 13  # 다음 단계(방 크기 질문)로 이동
            
            # 응답 생성
            response = f"원하시는 방 크기가 있으신가요? (예: 5평 이하, 5~10평, 10~15평, 15~20평, 20평 이상, 상관없음)"
        
        elif current_step == 13:  # 매물 특성 질문 - 방 크기
            # 방 크기 처리 - 키워드 기반 분석
            lower_msg = user_message.lower()
            if "5평" in lower_msg and "이하" in lower_msg:
                room_size = "5평 이하"
            elif "5" in lower_msg and "10" in lower_msg or "5~10" in lower_msg:
                room_size = "5~10평"
            elif "10" in lower_msg and "15" in lower_msg or "10~15" in lower_msg:
                room_size = "10~15평"
            elif "15" in lower_msg and "20" in lower_msg or "15~20" in lower_msg:
                room_size = "15~20평"
            elif "20평" in lower_msg and "이상" in lower_msg:
                room_size = "20평 이상"
            elif "상관" in lower_msg or "없" in lower_msg:
                room_size = "상관없음"
            else:
                # 숫자만 있는 경우 (예: "10평")
                extracted = self._extract_numbers(user_message)
                if extracted:
                    size = int(extracted)
                    if size <= 5:
                        room_size = "5평 이하"
                    elif 5 < size <= 10:
                        room_size = "5~10평"
                    elif 10 < size <= 15:
                        room_size = "10~15평"
                    elif 15 < size <= 20:
                        room_size = "15~20평"
                    else:
                        room_size = "20평 이상"
                else:
                    room_size = user_message  # 그대로 저장
            
            # 방 크기 저장
            data["property_preferences"]["room_size"] = room_size
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 14  # 다음 단계(방향 질문)로 이동
            
            # 응답 생성
            response = f"선호하시는 방향이 있으신가요? (예: 남향, 남동향, 동향, 남서향, 서향, 북향, 상관없음)"
        
        elif current_step == 14:  # 매물 특성 질문 - 방향
            # 방향 처리 - 키워드 기반 분석
            lower_msg = user_message.lower()
            if "남향" in lower_msg or "남" in lower_msg:
                direction = "남향"
            elif "남동" in lower_msg:
                direction = "남동향"
            elif "남서" in lower_msg:
                direction = "남서향"
            elif "동향" in lower_msg or "동" in lower_msg:
                direction = "동향"
            elif "서향" in lower_msg or "서" in lower_msg:
                direction = "서향"
            elif "북동" in lower_msg:
                direction = "북동향"
            elif "북서" in lower_msg:
                direction = "북서향"
            elif "북향" in lower_msg or "북" in lower_msg:
                direction = "북향"
            elif "상관" in lower_msg or "없" in lower_msg:
                direction = "상관없음"
            else:
                direction = user_message  # 그대로 저장
                
            # 방향 저장
            data["property_preferences"]["direction"] = direction
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 15  # 다음 단계(난방 종류 질문)로 이동
            
            # 응답 생성
            response = f"선호하시는 난방 종류가 있으신가요? (예: 개별난방, 중앙난방, 지역난방, 상관없음)"
            
        elif current_step == 15:  # 매물 특성 질문 - 난방 종류
            # 난방 종류 처리 - 키워드 기반 분석
            lower_msg = user_message.lower()
            if "개별" in lower_msg:
                heating_type = "개별난방"
            elif "중앙" in lower_msg:
                heating_type = "중앙난방"
            elif "지역" in lower_msg:
                heating_type = "지역난방"
            elif "상관" in lower_msg or "없" in lower_msg:
                heating_type = "상관없음"
            else:
                heating_type = user_message  # 그대로 저장
                
            # 난방 종류 저장
            data["property_preferences"]["heating_type"] = heating_type
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 16  # 다음 단계(주차 여부 질문)로 이동
            
            # 응답 생성
            response = f"주차 공간이 필요하신가요? (예/아니오/상관없음)"
            
        elif current_step == 16:  # 매물 특성 질문 - 주차 여부
            # 주차 여부 처리 - 키워드 기반 분석
            lower_msg = user_message.lower()
            if "예" in lower_msg or "네" in lower_msg or "필요" in lower_msg or "있" in lower_msg or "중요" in lower_msg:
                parking = True
                parking_pref = "있음"
            elif "아니" in lower_msg or "아뇨" in lower_msg or "불필요" in lower_msg or "없" in lower_msg:
                parking = False
                parking_pref = "없음"
            elif "상관" in lower_msg:
                parking = None  # 상관없음
                parking_pref = "상관없음"
            else:
                parking = "예" in user_message or "네" in user_message
                parking_pref = "있음" if parking else "없음"
                
            # 주차 여부 저장
            data["property_preferences"]["parking"] = parking
            data["property_preferences"]["parking_pref"] = parking_pref  # 표시용 텍스트도 저장
            
            # 상태 업데이트
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 17  # 다음 단계(엘리베이터 여부 질문)로 이동
            
            # 응답 생성
            response = f"엘리베이터가 필요하신가요? (있음/없음/상관없음)"
            
        elif current_step == 17:  # 매물 특성 질문 - 엘리베이터 여부
            # 엘리베이터 여부 처리 - 키워드 기반 분석
            lower_msg = user_message.lower()
            if "있" in lower_msg or "필요" in lower_msg or "네" in lower_msg or "예" in lower_msg or "중요" in lower_msg:
                elevator = True
                elevator_pref = "있음"
            elif "없" in lower_msg or "불필요" in lower_msg or "아니" in lower_msg:
                elevator = False
                elevator_pref = "없음"
            elif "상관" in lower_msg:
                elevator = None  # 상관없음
                elevator_pref = "상관없음"
            else:
                elevator = "있음" in user_message
                elevator_pref = "있음" if elevator else "없음"
                
            # 엘리베이터 여부 저장
            data["property_preferences"]["elevator"] = elevator
            data["property_preferences"]["elevator_pref"] = elevator_pref  # 표시용 텍스트도 저장
                
            # 상태 업데이트
            self.conversation_state["data"] = data
            
            # 추가 시설은 기본값으로 설정하고 건너뛰기
            data["property_preferences"]["facilities"] = "기본 시설"
            
            # 단계 19(최종 설정 확인)로 바로 이동
            self.conversation_state["step"] = 19
            
            # 모든 설정 정보 요약
            summary_parts = [
                "설정을 완료했습니다! 아래는 현재까지의 설정 요약입니다.",
                "",
                "## 예산 설정",
                f"- 월세: {data.get('monthly')}만원",
                f"- 보증금: {data.get('budget')}만원",
                f"- 관리비: {data.get('maintenance_fee')}만원",
                "",
                "## 검색 기준"
            ]
            
            if data.get("criteria") == "2":
                summary_parts.append(f"- 추천 기준: 반경")
                summary_parts.append(f"- 반경: {data.get('radius')}m")
            elif data.get("criteria") == "1":
                summary_parts.append(f"- 추천 기준: 소요시간")
                summary_parts.append(f"- 이동 방법: {data.get('movement', '도보')}")
                summary_parts.append(f"- 소요시간: {data.get('time_limit', '30')}분 이내")
            else:
                summary_parts.append(f"- 추천 기준: 상관없음")
            
            # 인프라 설정 정보
            summary_parts.append("")
            summary_parts.append("## 인프라 설정")
            
            infra_names = data.get("infra_names", [])
            for infra in infra_names:
                infra_detail = data.get("infra_details", {}).get(infra, {})
                importance = infra_detail.get("importance", "3")
                walk_time = infra_detail.get("walk_time", "10")
                frequency = infra_detail.get("frequency", "3")
                additional = infra_detail.get("additional_info", "")
                
                summary_parts.append(f"- {infra}")
                summary_parts.append(f"  - 중요도: {importance}/5")
                summary_parts.append(f"  - 도보 시간: {walk_time}분 이내")
                summary_parts.append(f"  - 이용 빈도: {frequency}/5")
                if additional:
                    summary_parts.append(f"  - 추가 정보: {additional}")
            
            # 매물 특성 설정 정보
            summary_parts.append("")
            summary_parts.append("## 매물 특성 설정")
            
            property_prefs = data.get("property_preferences", {})
            if property_prefs:
                for key, value in property_prefs.items():
                    # 추가 시설은 표시하지 않음
                    if key == "facilities":
                        continue
                    # 선호도 텍스트로 설정된 필드 사용
                    if key == "parking" and "parking_pref" in property_prefs:
                        continue
                    if key == "elevator" and "elevator_pref" in property_prefs:
                        continue
                        
                    label = {
                        "housing_type": "주거 타입",
                        "floor": "층수",
                        "room_size": "방 크기",
                        "direction": "방향",
                        "heating_type": "난방 종류",
                        "parking_pref": "주차 여부",
                        "elevator_pref": "엘리베이터 유무"
                    }.get(key, key)
                    
                    summary_parts.append(f"- {label}: {value}")
            
            # 설정 완료 메시지 및 검색 권장
            summary_parts.append("")
            summary_parts.append("설정하신 조건으로 매물을 검색하시겠어요? (예/아니오)")
            summary_parts.append("설정을 변경하고 싶으시면 변경하고 싶은 항목을 알려주세요.")
            
            response = "\n".join(summary_parts)
            
            # 즉시 매물 추천 검색은 하지 않고, 사용자 확인 후 검색하도록 변경
        
        elif current_step == 18:  # 매물 특성 질문 - 추가 시설
            # 이 단계는 스킵하므로 사용하지 않음, 필요한 경우 원래 코드 유지
            pass
            
        elif current_step == 19:  # 최종 설정 확인 및 추천 매물 검색
            # 사용자가 추천 매물 검색을 원하는지 확인
            if "예" in user_message or "네" in user_message or "검색" in user_message or "추천" in user_message:
                self.conversation_state["step"] = 20  # 추천 매물 검색 및 결과 단계로 이동
                response = "추천 매물을 검색 중입니다. 잠시만 기다려주세요..."
                
                # 설정된 정보를 사용하여 추천 매물 검색
                recommendations = self._search_recommendations()
                
                # 추천 결과를 대화 상태에 저장
                data["recommendations"] = recommendations
                self.conversation_state["data"] = data
                
                # 추천 결과가 있는 경우
                if recommendations and any(recommendations.values()):
                    # 결과 응답 생성
                    response = self._format_recommendations(recommendations)
                else:
                    # 추천 결과가 없는 경우 조건 완화하여 재검색
                    print("일치하는 매물이 없어 조건을 완화하여 재검색합니다...")
                    relaxed_recommendations = self._search_recommendations_relaxed()
                    
                    if relaxed_recommendations and any(relaxed_recommendations.values()):
                        data["recommendations"] = relaxed_recommendations
                        self.conversation_state["data"] = data
                        response = self._format_recommendations(relaxed_recommendations, is_relaxed=True)
                    else:
                        # 여전히 결과가 없는 경우 샘플 데이터 사용
                        print("완화된 조건으로도 매물을 찾지 못했습니다. 샘플 데이터를 사용합니다.")
                        sample_recommendations = self._get_sample_recommendations_data()
                        data["recommendations"] = sample_recommendations
                        self.conversation_state["data"] = data
                        response = self._format_recommendations(sample_recommendations, is_relaxed=True)
            
            # 설정 변경을 원하는 경우
            elif "변경" in user_message:
                # 변경하고자 하는 항목 감지
                if "월세" in user_message:
                    self.conversation_state["step"] = 1
                    response = f"월세 금액을 다시 설정해주세요. 현재 설정: {data.get('monthly')}만원"
                elif "보증금" in user_message:
                    self.conversation_state["step"] = 2
                    response = f"보증금 금액을 다시 설정해주세요. 현재 설정: {data.get('budget')}만원"
                elif "관리비" in user_message:
                    self.conversation_state["step"] = 3
                    response = f"관리비 금액을 다시 설정해주세요. 현재 설정: {data.get('maintenance_fee')}만원"
                elif "기준" in user_message:
                    self.conversation_state["step"] = 4
                    response = "어떤 기준으로 추천할까요?\n\n1. 소요시간 기준\n2. 반경 기준 (m 단위)\n3. 상관없음"
                elif "인프라" in user_message:
                    self.conversation_state["step"] = 6
                    response = "다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.\n\n1. 지하철역 - 대중교통 접근성\n2. 버스정류장 - 버스 노선 접근성\n3. 대형마트 - 쇼핑 및 생필품 구매\n4. 백화점 - 쇼핑 및 편의시설\n5. 편의점 - 생필품 및 간편식품\n6. 주민센터 - 행정 및 복지 서비스\n7. 다이소 - 생활용품 및 잡화\n8. 카페 - 휴식 및 업무 공간\n9. 공원 - 여가 및 산책 공간\n10. 우체국 - 우편 및 행정 서비스\n11. 헬스장 - 건강 관리 및 운동 시설\n12. 병원 - 의료 서비스\n13. 약국 - 의약품 구매\n14. 영화관 - 문화 및 엔터테인먼트\n15. PC방 - 게임 및 인터넷\n16. 노래방 - 엔터테인먼트\n17. 파출소/경찰서 - 치안 및 안전\n\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)"
                elif "매물" in user_message or "특성" in user_message:
                    self.conversation_state["step"] = 11
                    response = "선호하시는 주거 타입을 알려주세요. (예: 원룸, 투룸 둘 중 하나 택)"
                else:
                    # 변경할 항목이 명확하지 않은 경우
                    response = "어떤 항목을 변경하고 싶으신가요? (예: 월세, 보증금, 관리비, 추천 기준, 인프라, 매물 특성 등)"
            
            # 그 외의 경우 (예: 질문, 추가 요청 등)
            else:
                # 설정 정보를 기반으로 LLM을 통해 응답 생성
                context = {
                    "user_preferences": data
                }
                chat_history = self._get_chat_history()
                
                response = self.llm.generate_response(user_message, context, chat_history)
                
                # 이 응답을 채팅 이력에 추가
                self._add_to_chat_history(user_message, response)
        
        elif current_step == 20:  # 대화 모드 (추천 결과 이후)
            import re
            
            # 관심 매물 등록 요청인지 확인 - 정규표현식 사용
            match = re.search(r'(\d+)번?\s*매물\s*(관심|찜)', user_message)
            if match:
                property_number = int(match.group(1))
                print(f"[DEBUG] 관심 매물 등록 요청 - 매물 번호: {property_number}")
                
                # 관심 매물 등록 처리
                success = self._add_to_favorites(property_number)
                if success:
                    response = f"{property_number}번 매물을 관심 매물로 등록했습니다. 관심 매물은 '관심 매물 보기'를 통해 확인하실 수 있습니다."
                else:
                    response = f"관심 매물 등록에 실패했습니다. 매물 번호를 다시 확인해주세요."
            
            # 매물 상세 정보 요청인지 확인
            elif any(term in user_message.lower() for term in ["매물", "물건", "집"]) and any(str(i) in user_message for i in range(1, 20)):
                # 매물 번호 추출
                property_number = None
                for i in range(1, 20):
                    if str(i) in user_message:
                        property_number = i
                        break
                
                if property_number:
                    # 매물 상세 정보 응답 생성
                    response = self._get_property_detail(property_number)
                else:
                    response = "어떤 매물에 대해 더 자세한 정보를 원하시나요? 숫자로 알려주세요."
            
            # 관심 매물 목록 보기 요청인지 확인
            elif any(term in user_message.lower() for term in ["관심 매물 보기", "관심 목록", "관심 매물 목록", "찜 목록"]):
                # 관심 매물 목록 가져오기
                favorites = self._get_favorites()
                if favorites:
                    response = self._format_favorites(favorites)
                else:
                    response = "등록된 관심 매물이 없습니다."
                    
            # 추천 결과 다시 보기 요청인지 확인
            elif "다시" in user_message.lower() and any(term in user_message.lower() for term in ["결과", "추천", "매물"]):
                recommendations = data.get("recommendations", {})
                if recommendations and any(recommendations.values()):
                    response = self._format_recommendations(recommendations)
                else:
                    response = "저장된 추천 결과가 없습니다. 새로운 검색을 진행하시겠어요?"
            
            # 조건 변경 요청인지 확인
            elif "조건" in user_message.lower() and "변경" in user_message.lower():
                self.conversation_state["step"] = 19  # 설정 확인 단계로 이동
                
                # 설정 요약 보여주기
                response = "어떤 조건을 변경하고 싶으신가요? (예: 월세, 보증금, 관리비, 추천 기준, 인프라, 매물 특성 등)"
            
            # 추가 검색 요청인지 확인
            elif any(term in user_message.lower() for term in ["다시 검색", "재검색", "새로운 검색", "새로 검색"]):
                self.conversation_state["step"] = 19  # 설정 확인 단계로 이동
                
                # 현재 설정 정보 요약
                summary_parts = [
                    "다시 검색을 진행할게요. 현재 설정된 조건은 다음과 같습니다.",
                    "",
                    "## 예산 설정",
                    f"- 월세: {data.get('monthly')}만원",
                    f"- 보증금: {data.get('budget')}만원",
                    f"- 관리비: {data.get('maintenance_fee')}만원",
                    "",
                    "설정하신 조건으로 검색하시겠어요? 아니면 변경하실 조건이 있으신가요? (예/변경)"
                ]
                
                response = "\n".join(summary_parts)
            
            # 그 외의 경우 - LLM을 통한 응답 생성
            else:
                context = {
                    "user_preferences": data,
                    "recommendations": data.get("recommendations", {})
                }
                chat_history = self._get_chat_history()
                
                response = self.llm.generate_response(user_message, context, chat_history)
                
                # 이 응답을 채팅 이력에 추가
                self._add_to_chat_history(user_message, response)
        
        else:
            # 알 수 없는 단계인 경우 (오류 상황)
            response = "죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해주세요."
            # 초기 단계로 리셋
            self.conversation_state["step"] = 1
        
        # 대화 상태 저장
        self._save_conversation_state()
        
        # 디버그 로그 출력
        print(f"[DEBUG] 메시지 처리 완료 - 응답: {response[:100]}...")
        print(f"[DEBUG] 저장된 대화 단계: {self.conversation_state.get('step', 1)}")
        
        return response
    
    def _process_after_infra_questions(self, current_idx, infra_names):
        """인프라 질문 후 다음 단계 처리"""
        data = self.conversation_state.get("data", {})
        
        print(f"[DEBUG] 인프라 질문 후 처리 - 현재 인덱스: {current_idx}, 전체 인프라: {infra_names}")
        
        # 다음 인프라가 있는지 확인
        next_idx = current_idx + 1
        if next_idx < len(infra_names):
            # 다음 인프라에 대한 질문으로 이동
            data["current_infra_idx"] = next_idx
            self.conversation_state["data"] = data
            self.conversation_state["step"] = 7  # 인프라 중요도 질문으로 이동
            
            print(f"[DEBUG] 다음 인프라로 이동: {next_idx}, {infra_names[next_idx]}")
            
            # 다음 인프라에 대한 질문 생성
            next_infra = infra_names[next_idx]
            return f"{next_infra}에 대한 질문입니다.\n이 시설이 얼마나 중요한가요? (1: 별로 중요하지 않음 ~ 5: 매우 중요함)"
        else:
            # 모든 인프라 질문이 끝난 경우, 매물 특성 질문으로 이동
            self.conversation_state["step"] = 11
            
            print(f"[DEBUG] 모든 인프라 질문 완료, 매물 특성 질문으로 이동 (단계 11)")
            
            # 매물 특성 질문에 대한 응답 생성
            monthly = data.get("monthly", "60")
            budget = data.get("budget", "1000")
            maintenance_fee = data.get("maintenance_fee", "15")
            
            response_parts = [
                "인프라 설정이 완료되었습니다.",
                "",
                "## 현재까지의 설정 요약",
                "",
                f"- 월세: {monthly}만원",
                f"- 보증금: {budget}만원",
                f"- 관리비: {maintenance_fee}만원"
            ]
            
            if data.get("criteria") == "2":
                response_parts.append(f"- 추천 기준: 반경")
                response_parts.append(f"- 반경: {data.get('radius')}m")
            elif data.get("criteria") == "1":
                response_parts.append(f"- 추천 기준: 소요시간")
                response_parts.append(f"- 이동 방법: {data.get('movement', '도보')}")
                response_parts.append(f"- 소요시간: {data.get('time_limit', '30')}분 이내")
            else:
                response_parts.append(f"- 추천 기준: 상관없음")
            
            response_parts.append(f"- 선택한 인프라: {', '.join(data.get('infra_names', []))}")
            
            # 인프라 설정 세부 정보 추가
            response_parts.append("")
            response_parts.append("## 인프라 설정 세부 정보")
            for infra_name in infra_names:
                infra_detail = data.get("infra_details", {}).get(infra_name, {})
                response_parts.append(f"- {infra_name}:")
                for key, value in infra_detail.items():
                    label = {"importance": "중요도", "walk_time": "도보 시간", "frequency": "이용 빈도"}.get(key, key)
                    response_parts.append(f"  - {label}: {value}")
            
            response_parts.append("")
            response_parts.append("이제 원하시는 매물의 특성에 대해 알려주세요.")
            response_parts.append("선호하시는 주거 타입을 알려주세요. (예: 원룸, 투룸 둘 중 하나 택)")
            
            return "\n".join(response_parts)
    
    def _search_recommendations(self):
        """추천 매물 검색"""
        try:
            # 추천 서비스 호출
            data = self.conversation_state.get("data", {})
            
            # 사용자 상태 업데이트
            user_state = self.user_state
            user_state.budget = int(data.get("budget", 1000))
            user_state.monthly_rent = int(data.get("monthly", 60))
            user_state.maintenance_fee = int(data.get("maintenance_fee", 15))
            
            infra_preferences = data.get("infra_preferences", {})
            print(f"설정된 인프라 선호도: {infra_preferences}")  # 디버깅용
            
            # UserState 객체에 직접 인프라 선호도 설정
            self.user_state.infra_preferences = infra_preferences
            # 또는 update 메서드를 통해 설정
            self.user_state.update("infra_preferences", infra_preferences)
            
            # 확실히 인프라 선호도 확인하고 설정 - 추가된 부분
            if not infra_preferences and 'infra_details' in data:
                # infra_preferences가 비어있고 infra_details가 있는 경우
                print("인프라 선호도가 비어있어 infra_details에서 생성합니다.")
                infra_preferences = {}
                for infra_name, details in data.get("infra_details", {}).items():
                    importance = int(details.get("importance", 3))
                    # 인프라 코드 가져오기
                    infra_code = self._get_infra_code(infra_name)
                    if infra_code:
                        # 가중치 설정 (중요도에 따라)
                        infra_preferences[infra_code] = importance
                
                print(f"infra_details에서 생성된 인프라 선호도: {infra_preferences}")
            
            # 인프라 선호도 설정
            user_state.infra_preferences = infra_preferences
            
            # 위치 정보 설정 - 사용자 DB에서 가져오기
            conn = None
            try:
                conn = self._get_db_connection()
                cur = conn.cursor()
                
                # 사용자 UUID로 위치 정보 조회
                cur.execute(
                    "SELECT preferred_area, latitude, longitude, address FROM users WHERE user_uuid = %s",
                    (self.user_uuid,)
                )
                
                location_info = cur.fetchone()
                cur.close()
                
                if location_info and location_info[1] and location_info[2]:
                    # DB에 위치 정보가 있으면 사용
                    user_state.location_name = location_info[0]  # preferred_area
                    user_state.lat = float(location_info[1])     # latitude
                    user_state.lng = float(location_info[2])     # longitude
                    user_state.address = location_info[3]        # address
                    print(f"사용자 DB에서 위치 정보 로드: {user_state.location_name}, 좌표: ({user_state.lat}, {user_state.lng}), 주소: {user_state.address}")
                    
                else:
                    # DB에 정보가 없으면 기본값 설정
                    print("사용자 위치 정보가 없습니다. 기본값을 사용합니다.")
                    user_state.location_name = "서울시청"
                    user_state.lat = 37.566826
                    user_state.lng = 126.9786567
                    user_state.address = "서울 중구"
                    
            except Exception as e:
                print(f"위치 정보 로드 오류: {e}")
                # 오류 시 기본값 설정
                user_state.location_name = "서울시청"
                user_state.lat = 37.566826
                user_state.lng = 126.9786567
                user_state.address = "서울 중구"
            finally:
                if conn:
                    conn.close()
            
            # 추천 기준 설정
            criteria = data.get("criteria", "3")
            print(f"설정된 기준: {criteria}")

            if criteria == "2":  # 반경 기준
                radius = int(data.get("radius", 2000))
                user_state.search_radius = radius
                user_state.service = "반경"
                print(f"반경 기준 설정: {radius}m, service={user_state.service}")
            elif criteria == "1":  # 소요 시간 기준
                user_state.service = "소요시간"
                user_state.movement = data.get("movement", "도보")
                user_state.time_limit = int(data.get("time_limit", 30))
                print(f"소요시간 기준 설정: {user_state.movement} {user_state.time_limit}분, service={user_state.service}")
            else:  # 상관없음
                user_state.service = "상관없음"
                print(f"상관없음 기준 설정: service={user_state.service}")
                
            self.recommender.user_state.service = user_state.service
            
            # 인프라 선호도 설정
            infra_preferences = {}
            for infra_name, details in data.get("infra_details", {}).items():
                importance = int(details.get("importance", 3))
                # 인프라 코드 가져오기
                infra_code = self._get_infra_code(infra_name)
                if infra_code:
                    # 가중치 설정 (중요도에 따라)
                    weight = importance
                    infra_preferences[infra_code] = weight
            
            user_state.infra_preferences = infra_preferences
            
            # 추천 서비스에 인프라 선호도 전달
            self.recommender.user_state.infra_preferences = user_state.infra_preferences
            print(f"최종 인프라 선호도: {user_state.infra_preferences}")
            
            # 매물 특성 설정
            property_prefs = data.get("property_preferences", {})
            if property_prefs:
                # 속성 이름을 API에 맞게 변환
                property_features = {}
                
                # 주거 타입
                if "housing_type" in property_prefs:
                    property_features["type"] = property_prefs["housing_type"]
                
                # 층수
                if "floor" in property_prefs:
                    property_features["floor"] = property_prefs["floor"]
                
                # 방 크기
                if "room_size" in property_prefs:
                    property_features["size"] = property_prefs["room_size"]
                
                # 방향
                if "direction" in property_prefs:
                    property_features["direction"] = property_prefs["direction"]
                
                # 난방 종류
                if "heating_type" in property_prefs:
                    property_features["heating"] = property_prefs["heating_type"]
                
                # 주차 여부
                if "parking_pref" in property_prefs:
                    property_features["parking"] = property_prefs["parking_pref"]
                elif "parking" in property_prefs:
                    property_features["parking"] = "있음" if property_prefs["parking"] else "없음"
                
                # 엘리베이터 여부
                if "elevator_pref" in property_prefs:
                    property_features["elevator"] = property_prefs["elevator_pref"]
                elif "elevator" in property_prefs:
                    property_features["elevator"] = "있음" if property_prefs["elevator"] else "없음"
                
                # 여기가 중요한 부분입니다! 필수 수정 사항
                # user_state에 property_features 설정
                try:
                    user_state.property_features = property_features
                    print("user_state.property_features 설정 완료!")
                except AttributeError:
                    # property_features 속성이 없으면 추가
                    setattr(user_state, 'property_features', property_features)
                    print("setattr로 user_state.property_features 설정 완료!")
                
                # 이미 설정된 속성을 recommender에 전달
                try:
                    self.recommender.user_state.property_features = property_features
                    print("recommender.user_state.property_features 설정 완료!")
                except AttributeError:
                    # property_features 속성이 없으면 추가
                    setattr(self.recommender.user_state, 'property_features', property_features)
                    print("setattr로 recommender.user_state.property_features 설정 완료!")
                
                # 대신 직접 property_features 설정
                self.recommender.property_features = property_features
            
            # 추천 서비스 호출 - RealEstateRecommender의 get_recommendations 메소드 사용
            result = self.recommender.get_recommendations()
            
            # 추천 결과를 데이터베이스에 저장 (추가)
            self._save_recommendations_to_db(result)
            
            # 디버깅 정보 출력
            print(f"DEBUG: user_state.property_features: {getattr(user_state, 'property_features', None)}")
            print(f"DEBUG: recommender.user_state.property_features: {getattr(self.recommender.user_state, 'property_features', None)}")
            print(f"DEBUG: recommender.property_features: {getattr(self.recommender, 'property_features', None)}")
            print(f"DEBUG: recommender.user_state.infra_preferences: {getattr(self.recommender.user_state, 'infra_preferences', None)}")
            
            return result
        
        except Exception as e:
            print(f"추천 매물 검색 오류: {e}")
            return {}

    def _search_recommendations_relaxed(self):
        """완화된 조건으로 추천 매물 검색"""
        try:
            # 사용자 상태의 복사본 생성
            relaxed_user_state = copy.deepcopy(self.user_state)
            
            # 예산 조건 완화 (20% 증가)
            relaxed_user_state.monthly_rent = int(relaxed_user_state.monthly_rent * 1.2)
            relaxed_user_state.budget = int(relaxed_user_state.budget * 1.2)
            relaxed_user_state.maintenance_fee = int(relaxed_user_state.maintenance_fee * 1.2)
            
            # 검색 반경 확대 (50% 증가)
            if hasattr(relaxed_user_state, 'search_radius'):
                relaxed_user_state.search_radius = int(relaxed_user_state.search_radius * 1.5)
                
            # 소요시간 증가 (30% 증가)
            if hasattr(relaxed_user_state, 'time_limit'):
                relaxed_user_state.time_limit = int(relaxed_user_state.time_limit * 1.3)
            
            # 인프라 도보 시간 증가 (30% 증가)
            property_prefs = relaxed_user_state.property_preferences
            for key in property_prefs:
                if key.endswith('walk_time'):
                    property_prefs[key] = int(property_prefs[key] * 1.3)
            
            # 원래 user_state 임시 저장
            original_user_state = self.recommender.user_state
            
            # 완화된 user_state 설정
            self.recommender.user_state = relaxed_user_state
            
            # 추천 호출
            result = self.recommender.get_recommendations()
            
            # 원래 user_state 복원
            self.recommender.user_state = original_user_state
            
            return result
            
        except Exception as e:
            print(f"완화된 조건 추천 매물 검색 오류: {e}")
            return {}
    
    def _get_infra_type(self, infra_name):
        """인프라 이름에 해당하는 API 호출용 인프라 타입 반환"""
        infra_type_mapping = {
            "지하철역": "traffic_subway",
            "버스정류장": "traffic_bus",
            "대형마트": "life_mart",
            "백화점": "life_department_store",
            "편의점": "life_convenience_store",
            "주민센터": "life_community_center",
            "다이소": "life_daiso",
            "카페": "life_cafe",
            "공원": "life_park",
            "우체국": "life_post_office",
            "헬스장": "life_healthjang",
            "병원": "health_hospital",
            "약국": "health_pharmacy",
            "영화관": "play_cinema",
            "PC방": "play_pc_cafe",
            "노래방": "play_karaoke",
            "파출소/경찰서": "safety_police_station"
        }
        
        return infra_type_mapping.get(infra_name, "other")
    
    def _format_recommendations(self, recommendations, is_relaxed=False):
        """추천 결과 포맷팅"""
        data = self.conversation_state.get("data", {})
        monthly = data.get("monthly", "60")
        budget = data.get("budget", "1000")
        maintenance_fee = data.get("maintenance_fee", "15")
        
        result_parts = ["# ============================================================"]
        result_parts.append("📋 추천 매물 정보 요약\n")
        
        # 조건 완화 안내 메시지 (필요한 경우)
        if is_relaxed:
            result_parts.append("⚠️ 입력하신 조건에 정확히 맞는 매물이 없어 다음 조건을 완화하여 검색했습니다:")
            result_parts.append("  - 예산(월세, 보증금, 관리비): 20% 증가")
            result_parts.append("  - 검색 반경: 50% 증가")
            result_parts.append("  - 소요시간: 30% 증가\n")
        
        result_parts.append(f"💰 [예산 정보]")
        result_parts.append(f"월세: {monthly}만원")
        result_parts.append(f"보증금: {budget}만원")
        result_parts.append(f"관리비: {maintenance_fee}만원\n")
        
        # 위치 정보 추가
        result_parts.append(f"📍 [거주지 정보]")
        if data.get("criteria") == "2":  # 반경 기준
            result_parts.append(f"반경: {data.get('radius', '2000')}m")
        elif data.get("criteria") == "1":  # 소요시간 기준
            movement = data.get("movement", "도보")
            time_limit = data.get("time_limit", "30")
            result_parts.append(f"소요시간: {time_limit}분 이내 ({movement})")
        else:  # 상관없음
            result_parts.append(f"추천 기준: 상관없음")
            
        # 매물 위치 정보 (사용자 DB에서 가져온 정보가 있다면)
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "SELECT preferred_area, address FROM users WHERE user_uuid = %s",
                (self.user_uuid,)
            )
            location_info = cur.fetchone()
            cur.close()
            conn.close()
            
            if location_info:
                if location_info[0]:  # preferred_area
                    result_parts.append(f"선호 지역: {location_info[0]}")
                if location_info[1]:  # address
                    result_parts.append(f"주소: {location_info[1]}")
        except Exception as e:
            print(f"위치 정보 로드 오류 (무시됨): {e}")
        
        if not recommendations or not any(recommendations.values()):
            result_parts.append("\n❗ 현재 설정하신 조건에 맞는 매물을 찾지 못했습니다.")
            result_parts.append("\n💡 추천 사항:")
            result_parts.append("  1. 예산 범위를 넓혀보세요 (월세, 보증금 상향 조정)")
            result_parts.append("  2. 검색 범위를 넓혀보세요 (반경 확대 또는 소요시간 증가)")
            result_parts.append("  3. 다른 인프라 유형이나 특성을 고려해보세요")
            return "\n".join(result_parts)
        
        # 각 타입별 추천 매물 정보 포맷팅
        combined_count = 0  # 종합 추천 매물 수 카운트
        
        # 종합 추천 매물 분리 (예산 내/초과)
        within_budget = []
        exceeds_budget = []
        
        if recommendations.get("combined"):
            for prop in recommendations["combined"]:
                if prop.get("budget_exceeded", False):
                    exceeds_budget.append(prop)
                else:
                    within_budget.append(prop)
                    
            combined_count = len(within_budget) + len(exceeds_budget)
        
        # 예산 내 종합 추천 매물
        if within_budget:
            result_parts.append(f"\n🏠 [예산 위치 내 종합 추천 매물]")
            for i, prop in enumerate(within_budget, 1):
                result_parts.extend(self._format_property_details(prop, i))
        
        # 예산 초과 종합 추천 매물
        if exceeds_budget:
            result_parts.append(f"\n⚠️ [예산 초과 종합 추천 매물]")
            start_idx = len(within_budget) + 1
            for i, prop in enumerate(exceeds_budget, start_idx):
                # 초과 금액 정보 추가
                budget_info = []
                if prop.get("rent_exceeded") and prop.get("rent_excess") > 0:
                    budget_info.append(f"월세 {prop.get('rent_excess')}만원 초과")
                if prop.get("deposit_exceeded") and prop.get("deposit_excess") > 0:
                    budget_info.append(f"보증금 {prop.get('deposit_excess')}만원 초과")
                if prop.get("maint_exceeded") and prop.get("maint_excess") > 0:
                    budget_info.append(f"관리비 {prop.get('maint_excess')}만원 초과")
                
                # 매물 정보에 초과 정보 추가
                property_lines = self._format_property_details(prop, i)
                if budget_info:
                    property_lines.insert(2, f"⚠️ 예산 초과: {', '.join(budget_info)}")
                
                result_parts.extend(property_lines)
        
        # 위치 기반 추천 매물 - 최대 3개만 표시
        if recommendations.get("location_based") and len(recommendations["location_based"]) > 0:
            location_props = recommendations["location_based"][:3]
            result_parts.append(f"\n🏠 [거주지 기반 추천 매물]")
            for i, prop in enumerate(location_props, 1):
                result_parts.extend(self._format_property_details(prop, i))
        
        # 예산 기반 추천 매물 - 최대 3개만 표시
        if recommendations.get("budget_based") and len(recommendations["budget_based"]) > 0:
            budget_props = recommendations["budget_based"][:3]
            result_parts.append(f"\n🏠 [예산 기반 추천 매물]")
            for i, prop in enumerate(budget_props, 1):
                result_parts.extend(self._format_property_details(prop, i))
        
        # 추가 정보 및 도움말
        result_parts.append("\n더 자세한 정보를 원하시는 매물이 있다면 번호로 알려주세요. (예: '1번 매물에 대해 더 알고 싶어요')")
        result_parts.append("관심 있는 매물은 '2번 매물 관심 등록' 형태로 알려주시면 관심 매물로 저장해드립니다.")
        result_parts.append("'관심 매물 보기'를 입력하시면 저장한 관심 매물을 확인하실 수 있습니다.")
        
        return "\n".join(result_parts)
    
    def _format_property_details(self, prop, index):
        """개별 매물 정보를 포맷팅"""
        property_lines = []
        
        # 기본 정보
        infra_score = prop.get("infra_score", 0)
        feature_score = prop.get("feature_score", 0)
        total_score = infra_score + feature_score
        
        property_lines.append(f"\n{index}. 📌 {prop['address']} ({prop['station']})")
        property_lines.append(f"💸 월세: {prop['rent']}만원 | 보증금: {prop['deposit']}만원 | 관리비: {prop['maint']}만원")
        property_lines.append(f"🚶 {prop['time_info']}")
        property_lines.append(f"⭐ 총점: {total_score:.1f}/10.0 = 인프라({infra_score:.1f}/3.0) + 특성({feature_score:.1f}/7.0)")
        
        property_lines.append(f"🏢 층수: {prop['floor']}| 면적: {prop.get('size', '?')}평")
        property_lines.append(f"🔥 난방: {prop['heating_type']}| 방향: {prop.get('direction', prop.get('view', '?'))}")
        property_lines.append(f"🅿️ 주차: {'가능' if prop['parking'] else '불가능'}| 엘리베이터: {'있음' if prop.get('elevator', False) else '없음'}")
        property_lines.append(f"🏠 타입: {prop.get('type', '원룸')}")
        
        if prop.get("facilities"):
            property_lines.append(f"🛋️ 시설: {prop['facilities']}")
        
        if prop.get("safety"):
            property_lines.append(f"🔒 안전: {prop['safety']}")
        
        # 인프라 세부 정보 추가
        if prop.get("infra_details"):
            property_lines.append("📊 주변 인프라:")
            for infra_type, detail in prop["infra_details"].items():
                if detail.get("nearest"):
                    property_lines.append(f"    - {infra_type}: {detail['nearest']} ({detail.get('distance', 0):.0f}m)")
                    
        return property_lines
    
    def _get_property_detail(self, property_number):
        """특정 매물의 상세 정보 가져오기"""
        try:
            data = self.conversation_state.get("data", {})
            recommendations = data.get("recommendations", {})
            
            # 모든 추천 매물을 하나의 리스트로 합치기
            all_properties = []
            for rec_type in ["combined", "location_based", "budget_based"]:
                if recommendations.get(rec_type):
                    all_properties.extend(recommendations[rec_type])
            
            # 요청한 번호의 매물 찾기
            if 1 <= property_number <= len(all_properties):
                prop = all_properties[property_number - 1]
                
                detail_parts = [f"## {property_number}번 매물 상세 정보\n"]
                detail_parts.append(f"주소: {prop['address']}")
                detail_parts.append(f"인근 역: {prop['station']}")
                detail_parts.append(f"월세: {prop['rent']}만원")
                detail_parts.append(f"보증금: {prop['deposit']}만원")
                detail_parts.append(f"관리비: {prop['maint']}만원")
                detail_parts.append(f"교통 정보: {prop['time_info']}")
                detail_parts.append(f"층수: {prop['floor']}")
                detail_parts.append(f"난방: {prop['heating_type']}")
                detail_parts.append(f"주차: {'가능' if prop['parking'] else '불가능'}")
                detail_parts.append(f"엘리베이터: {'있음' if prop.get('elevator', False) else '없음'}")
                detail_parts.append(f"면적: {prop.get('size', '?')}평")
                detail_parts.append(f"방향: {prop.get('direction', prop.get('view', '방향 정보 없음'))}")
                detail_parts.append(f"타입: {prop.get('type', '원룸')}")
                
                if prop.get("facilities"):
                    detail_parts.append(f"\n시설: {prop['facilities']}")
                
                if prop.get("safety"):
                    detail_parts.append(f"안전시설: {prop['safety']}")
                
                # 인프라 세부 정보 추가
                if prop.get("infra_details"):
                    detail_parts.append("\n### 인프라 세부 정보:")
                    for infra_type, detail in prop["infra_details"].items():
                        if detail.get("score", 0) > 0:
                            detail_parts.append(f"- {infra_type}: {detail['nearest']} (거리: {detail['distance']:.0f}m)")
                
                # 매물에 대한 추가 정보나 특징
                if prop.get("description"):
                    detail_parts.append(f"\n### 매물 설명:")
                    detail_parts.append(prop["description"])
                
                # 예산 초과 정보 (있는 경우)
                if prop.get("budget_exceeded"):
                    detail_parts.append("\n### 예산 초과 정보:")
                    if prop.get("rent_exceeded") and prop.get("rent_excess", 0) > 0:
                        detail_parts.append(f"- 월세: {prop['rent']}만원 (예산 {data.get('monthly')}만원 대비 {prop.get('rent_excess')}만원 초과)")
                    if prop.get("deposit_exceeded") and prop.get("deposit_excess", 0) > 0:
                        detail_parts.append(f"- 보증금: {prop['deposit']}만원 (예산 {data.get('budget')}만원 대비 {prop.get('deposit_excess')}만원 초과)")
                    if prop.get("maint_exceeded") and prop.get("maint_excess", 0) > 0:
                        detail_parts.append(f"- 관리비: {prop['maint']}만원 (예산 {data.get('maintenance_fee')}만원 대비 {prop.get('maint_excess')}만원 초과)")
                
                detail_parts.append("\n이 매물에 관심이 있으신가요? '관심 등록'을 입력하시면 관심 매물로 저장해드립니다.")
                detail_parts.append("다른 매물도 확인하시려면 '다시 검색'을 입력해주세요.")
                
                return "\n".join(detail_parts)
            else:
                return f"죄송합니다. {property_number}번 매물 정보를 찾을 수 없습니다."
        
        except Exception as e:
            print(f"매물 상세 정보 가져오기 오류: {e}")
            return "매물 정보를 가져오는 중 오류가 발생했습니다."
    
    def _get_infra_code(self, infra_name):
        """인프라 이름에 해당하는 코드 반환"""
        infra_name_to_code = {}
        
        # Config에서 인프라 타입 코드와 이름 매핑 생성
        for infra in Config.INFRA_TYPES:
            infra_name_to_code[infra["name"]] = infra["code"]
        
        # 매핑된 코드 반환
        return infra_name_to_code.get(infra_name)
    
    def _get_chat_history(self):
        """채팅 이력 가져오기"""
        conn = None
        try:
            if not self.user_uuid:
                return []
            
            conn = self._get_db_connection()
            cur = conn.cursor()
            
            # 최근 10개의 대화 기록 가져오기
            cur.execute("""
                SELECT message, response FROM chat_history
                WHERE user_uuid = %s
                ORDER BY created_at DESC
                LIMIT 10
            """, (self.user_uuid,))
            
            results = cur.fetchall()
            cur.close()
            
            # 채팅 이력 포맷팅
            chat_history = []
            for msg, resp in results:
                chat_history.append({
                    "user": msg,
                    "bot": resp
                })
            
            # 시간순으로 정렬 (가장 오래된 것부터)
            chat_history.reverse()
            
            return chat_history
            
        except Exception as e:
            print(f"채팅 이력 로드 오류: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def _add_to_chat_history(self, user_message, bot_response):
        """채팅 이력에 대화 추가"""
        if not self.user_uuid:
            print("사용자 ID가 없어 채팅 이력을 저장할 수 없습니다.")
            return
            
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            
            # 채팅 이력 저장
            cur.execute("""
                INSERT INTO chat_history (user_uuid, message, response)
                VALUES (%s, %s, %s)
            """, (self.user_uuid, user_message, bot_response))
            
            conn.commit()
            cur.close()
            print(f"사용자 {self.user_uuid}의 채팅 이력 저장 성공")
            
        except Exception as e:
            print(f"채팅 이력 저장 오류: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    
    def _add_to_favorites(self, property_number):
        """관심 매물 추가"""
        try:
            print(f"[DEBUG] 관심 매물 등록 시작 - 매물 번호: {property_number}")
            
            data = self.conversation_state.get("data", {})
            recommendations = data.get("recommendations", {})
            
            # 모든 추천 매물을 하나의 리스트로 합치기
            all_properties = []
            existing_ids = set()
            
            # 종합 추천 매물 추가 (우선순위 1)
            if recommendations.get("combined"):
                for prop in recommendations["combined"]:
                    prop_id = prop.get("id")
                    if prop_id and prop_id not in existing_ids:
                        all_properties.append(prop)
                        existing_ids.add(prop_id)
                    elif not prop_id:
                        all_properties.append(prop)
            
            # 위치 기반 추천 매물 추가 (우선순위 2)
            if recommendations.get("location_based"):
                for prop in recommendations["location_based"]:
                    prop_id = prop.get("id")
                    if prop_id and prop_id not in existing_ids:
                        all_properties.append(prop)
                        existing_ids.add(prop_id)
                    elif not prop_id:
                        all_properties.append(prop)
            
            # 예산 기반 추천 매물 추가 (우선순위 3)
            if recommendations.get("budget_based"):
                for prop in recommendations["budget_based"]:
                    prop_id = prop.get("id")
                    if prop_id and prop_id not in existing_ids:
                        all_properties.append(prop)
                        existing_ids.add(prop_id)
                    elif not prop_id:
                        all_properties.append(prop)
            
            print(f"[DEBUG] 전체 매물 수: {len(all_properties)}")
            
            # 요청한 번호의 매물 찾기 (1부터 시작)
            if 1 <= property_number <= len(all_properties):
                prop = all_properties[property_number - 1]
                print(f"[DEBUG] 선택된 매물: {prop.get('address')}")
                
                # 매물 ID 생성 (없는 경우)
                property_id = prop.get("id")
                if not property_id:
                    # 주소와 역 정보로 임시 ID 생성
                    import hashlib
                    temp_id = f"{prop.get('address', '')}_{prop.get('station', '')}_{prop.get('rent', 0)}"
                    property_id = hashlib.md5(temp_id.encode()).hexdigest()
                    prop["id"] = property_id
                    print(f"[DEBUG] 임시 ID 생성: {property_id}")
                
                # 관심 매물 저장
                conn = self._get_db_connection()
                cur = conn.cursor()
                
                print(f"[DEBUG] 데이터베이스 연결 성공")
                
                # 이미 저장된 매물인지 확인
                cur.execute(
                    "SELECT COUNT(*) FROM favorite_properties WHERE user_uuid = %s AND property_id = %s",
                    (self.user_uuid, property_id)
                )
                
                count = cur.fetchone()[0]
                print(f"[DEBUG] 기존 매물 중복 확인: {count}")
                
                if count > 0:
                    cur.close()
                    conn.close()
                    print(f"이미 등록된 관심 매물입니다: {property_id}")
                    return True  # 이미 등록된 경우도 성공으로 처리
                
                # 새 관심 매물 등록 - id 컬럼 제외 (자동 증가)
                print(f"[DEBUG] 관심 매물 등록 시작 - property_id: {property_id}")
                
                # 데이터 정리 및 타입 변환
                address = str(prop.get("address", ""))
                station = str(prop.get("station", ""))
                rent = int(prop.get("rent", 0))  # integer로 변환
                deposit = int(prop.get("deposit", 0))  # integer로 변환
                maint = int(prop.get("maint", 0))  # integer로 변환
                floor = str(prop.get("floor", ""))
                heating_type = str(prop.get("heating_type", ""))
                parking = bool(prop.get("parking", False))
                facilities = str(prop.get("facilities", ""))
                view = str(prop.get("view", prop.get("direction", "")))
                lat = prop.get("lat")
                lng = prop.get("lng")
                infra_score = float(prop.get("infra_score", 0))
                time_info = str(prop.get("time_info", ""))
                
                # lat, lng가 None인 경우 처리
                if lat is not None:
                    lat = float(lat)
                if lng is not None:
                    lng = float(lng)
                
                # id 컬럼을 제외하고 INSERT (자동 증가)
                cur.execute(
                    """INSERT INTO favorite_properties (
                        user_uuid, property_id, address, station, rent, deposit, maint, 
                        floor, heating_type, parking, facilities, view, lat, lng, 
                        infra_score, time_info, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())""",
                    (
                        self.user_uuid,
                        property_id,
                        address,
                        station,
                        rent,
                        deposit,
                        maint,
                        floor,
                        heating_type,
                        parking,
                        facilities,
                        view,
                        lat,
                        lng,
                        infra_score,
                        time_info
                    )
                )
                
                conn.commit()
                cur.close()
                conn.close()
                
                print(f"[DEBUG] 관심 매물 등록 성공: {address}")
                return True
            else:
                print(f"[DEBUG] 매물 번호 범위 초과: {property_number}, 전체 매물 수: {len(all_properties)}")
                return False
                
        except Exception as e:
            print(f"[DEBUG] 관심 매물 등록 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_favorites(self):
        """사용자의 관심 매물 목록 가져오기"""
        if not self.user_uuid:
            print("사용자 ID가 없어 관심 매물을 가져올 수 없습니다.")
            return []
            
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # 관심 매물 목록 조회
            cur.execute(
                """SELECT id, property_id, address, station, rent, deposit, maint, 
                        floor, heating_type, parking, facilities, view, 
                        lat, lng, infra_score, time_info, created_at 
                FROM favorite_properties 
                WHERE user_uuid = %s 
                ORDER BY created_at DESC""",
                (self.user_uuid,)
            )
            
            favorites = cur.fetchall()
            cur.close()
            conn.close()
            
            print(f"[DEBUG] 관심 매물 {len(favorites)}개 조회")
            return [dict(fav) for fav in favorites]
            
        except Exception as e:
            print(f"관심 매물 목록 가져오기 오류: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def _format_favorites(self, favorites):
        """관심 매물 목록 포맷팅"""
        if not favorites:
            return "등록된 관심 매물이 없습니다."
            
        result_parts = ["# 관심 매물 목록\n"]
        
        for i, fav in enumerate(favorites, 1):
            result_parts.append(f"{i}. 📌 {fav.get('address')}")
            result_parts.append(f"   🚇 {fav.get('station')}")
            result_parts.append(f"   💸 월세: {fav.get('rent')}만원 | 보증금: {fav.get('deposit')}만원 | 관리비: {fav.get('maint')}만원")
            result_parts.append(f"   🏢 {fav.get('floor')} | 난방: {fav.get('heating_type')}")
            result_parts.append(f"   🅿️ 주차: {'가능' if fav.get('parking') else '불가능'}")
            if fav.get('time_info'):
                result_parts.append(f"   🚶 {fav.get('time_info')}")
            created_at = fav.get('created_at')
            if created_at:
                result_parts.append(f"   📅 등록일: {created_at.strftime('%Y-%m-%d %H:%M')}")
            result_parts.append("")
        
        result_parts.append("관심 매물을 삭제하시려면 '관심 매물 삭제 [번호]'를 입력해주세요.")
        return "\n".join(result_parts)
    
    def _get_sample_recommendations_data(self):
        """샘플 추천 매물 데이터를 딕셔너리 형태로 반환"""
        # 현재 사용자 설정 값 가져오기
        data = self.conversation_state.get("data", {})
        monthly = int(data.get("monthly", "60"))
        budget = int(data.get("budget", "1000"))
        
        # 샘플 매물 데이터
        sample_properties = {
            "combined": [
                {
                    "address": "서울 동작구 노량진동 209-1",
                    "station": "노량진역",
                    "rent": int(monthly * 0.7),  # 예산의 70%
                    "deposit": int(budget * 0.3),  # 보증금의 30%
                    "maint": 3,
                    "time_info": "도보 5.0분",
                    "infra_score": 3.0,
                    "feature_score": 6.3,
                    "floor": "2층 (저층(1-3층))",
                    "size": "5.0평",
                    "heating_type": "중앙난방",
                    "direction": "남",
                    "parking": True,
                    "elevator": False,
                    "type": "원룸",
                    "facilities": "벽걸이형, 침대, 책상, 옷장, 신발장, 냉장고, 세탁기, 인덕션, 전자레인지",
                    "safety": "현관보안",
                    "infra_details": {
                        "편의점": {"nearest": "씨유노량진고시촌점", "distance": 105, "score": 1.0},
                        "지하철역": {"nearest": "01호선 노량진역", "distance": 345, "score": 1.0},
                        "대형마트": {"nearest": "홈플러스 익스프레스 상도2점", "distance": 573, "score": 1.0}
                    }
                },
                {
                    "address": "서울 동작구 신대방동 339-6",
                    "station": "신대방삼거리역",
                    "rent": int(monthly * 0.4),  # 예산의 40%
                    "deposit": int(budget * 0.1),  # 보증금의 10%
                    "maint": 9,
                    "time_info": "도보 4.0분",
                    "infra_score": 3.0,
                    "feature_score": 5.2,
                    "floor": "2층 (저층(1-3층))",
                    "size": "5.0평",
                    "heating_type": "개별난방",
                    "direction": "남",
                    "parking": True,
                    "elevator": False,
                    "type": "원룸",
                    "facilities": "벽걸이형, 침대, 책상, 옷장, 신발장, 냉장고, 세탁기, 싱크대, 인덕션, 전자레인지, 붙박이장",
                    "safety": "화재경보기, 비디오폰, 인터폰, CCTV, 현관보안, 방범창",
                    "infra_details": {
                        "편의점": {"nearest": "씨유(신대방점)", "distance": 129, "score": 1.0},
                        "대형마트": {"nearest": "이마트에브리데이 대방동점", "distance": 250, "score": 1.0},
                        "지하철역": {"nearest": "07호선 신대방삼거리역", "distance": 255, "score": 1.0}
                    }
                },
                {
                    "address": "서울 강남구 역삼동 123-45",
                    "station": "강남역",
                    "rent": int(monthly * 1.2),  # 예산의 120%
                    "deposit": int(budget * 0.5),  # 보증금의 50%
                    "maint": 10,
                    "time_info": "도보 5분",
                    "infra_score": 2.5,
                    "feature_score": 5.5,
                    "total_score": 8.0,
                    "floor": "5층",
                    "heating_type": "개별난방",
                    "parking": True,
                    "elevator": True,
                    "facilities": "에어컨, 냉장고, 세탁기",
                    "view": "남향, 채광 좋음",
                    "size": 8,
                    "type": "원룸",
                    "safety": "현관보안",
                    "infra_details": {
                        "지하철역": {"nearest": "강남역", "distance": 350, "score": 1.0},
                        "공원": {"nearest": "역삼공원", "distance": 450, "score": 0.7},
                        "헬스장": {"nearest": "역삼헬스센터", "distance": 200, "score": 0.8}
                    },
                    "budget_exceeded": True,
                    "rent_exceeded": True,
                    "rent_excess": int(monthly * 0.2)
                }
            ],
            "location_based": [
                {
                    "address": "서울 강남구 역삼동 456-78",
                    "station": "역삼역",
                    "rent": int(monthly * 0.9),
                    "deposit": int(budget * 0.4),
                    "maint": 8,
                    "time_info": "도보 3분",
                    "infra_score": 2.8,
                    "feature_score": 6.0,
                    "total_score": 8.8,
                    "floor": "4층",
                    "heating_type": "중앙난방",
                    "parking": True,
                    "elevator": True,
                    "facilities": "에어컨, 냉장고, 세탁기, 인덕션",
                    "view": "동향",
                    "size": 7,
                    "type": "원룸",
                    "safety": "CCTV, 현관보안",
                    "infra_details": {
                        "지하철역": {"nearest": "역삼역", "distance": 300, "score": 1.0},
                        "편의점": {"nearest": "CU역삼점", "distance": 150, "score": 0.9},
                        "카페": {"nearest": "스타벅스 역삼점", "distance": 200, "score": 0.9}
                    }
                }
            ],
            "budget_based": [
                {
                    "address": "서울 마포구 합정동 456-78",
                    "station": "합정역",
                    "rent": int(monthly * 0.6),
                    "deposit": int(budget * 0.3),
                    "maint": 8,
                    "time_info": "도보 7분",
                    "infra_score": 3.0,
                    "feature_score": 5.0,
                    "total_score": 8.0,
                    "floor": "3층",
                    "heating_type": "중앙난방",
                    "parking": False,
                    "elevator": True,
                    "facilities": "냉장고, 인덕션",
                    "view": "서향, 한강 조망",
                    "size": 6,
                    "type": "원룸",
                    "safety": "CCTV",
                    "infra_details": {
                        "지하철역": {"nearest": "합정역", "distance": 400, "score": 0.9},
                        "공원": {"nearest": "망원한강공원", "distance": 350, "score": 1.0},
                        "헬스장": {"nearest": "마포헬스클럽", "distance": 500, "score": 0.7}
                    }
                }
            ]
        }
        
        return sample_properties
    def _save_recommendations_to_db(self, recommendations):
        """추천 결과를 데이터베이스에 저장"""
        if not self.user_uuid or not recommendations:
            return
            
        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()
            
            # 기존 추천 결과 삭제 (사용자별)
            cur.execute("DELETE FROM location_recommendations WHERE user_uuid = %s", (self.user_uuid,))
            cur.execute("DELETE FROM budget_recommendations WHERE user_uuid = %s", (self.user_uuid,))
            cur.execute("DELETE FROM combined_recommendations WHERE user_uuid = %s", (self.user_uuid,))
            
            # 새 추천 결과 저장
            for rec_type, properties in recommendations.items():
                for i, prop in enumerate(properties):
                    if rec_type == "location_based":
                        # location_recommendations 테이블용
                        cur.execute("""
                            INSERT INTO location_recommendations (
                                user_uuid, property_id, address, station, rent, 
                                deposit, maint, lat, lng, infra_score, time_info, score, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """, (
                            self.user_uuid,
                            prop.get("id", f"{rec_type}_{i}"),
                            prop.get("address", ""),
                            prop.get("station", ""),
                            prop.get("rent", 0),
                            prop.get("deposit", 0),
                            prop.get("maint", 0),
                            prop.get("lat"),
                            prop.get("lng"),
                            prop.get("infra_score", 0),
                            prop.get("time_info", ""),
                            prop.get("total_score", 0)
                        ))
                    
                    elif rec_type == "budget_based":
                        # budget_recommendations 테이블용
                        cur.execute("""
                            INSERT INTO budget_recommendations (
                                user_uuid, property_id, address, station, rent, 
                                deposit, maint, lat, lng, infra_score, time_info, score, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """, (
                            self.user_uuid,
                            prop.get("id", f"{rec_type}_{i}"),
                            prop.get("address", ""),
                            prop.get("station", ""),
                            prop.get("rent", 0),
                            prop.get("deposit", 0),
                            prop.get("maint", 0),
                            prop.get("lat"),
                            prop.get("lng"),
                            prop.get("infra_score", 0),
                            prop.get("time_info", ""),
                            prop.get("total_score", 0)
                        ))
                    
                    elif rec_type == "combined":
                        # combined_recommendations 테이블용 (더 많은 컬럼)
                        cur.execute("""
                            INSERT INTO combined_recommendations (
                                user_uuid, property_id, address, station, rent, deposit, maint, 
                                floor, heating_type, parking, facilities, view, 
                                lat, lng, infra_score, time_info, score, created_at
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """, (
                            self.user_uuid,
                            prop.get("id", f"{rec_type}_{i}"),
                            prop.get("address", ""),
                            prop.get("station", ""),
                            prop.get("rent", 0),
                            prop.get("deposit", 0),
                            prop.get("maint", 0),
                            prop.get("floor", ""),
                            prop.get("heating_type", ""),
                            prop.get("parking", False),
                            prop.get("facilities", ""),
                            prop.get("view", prop.get("direction", "")),
                            prop.get("lat"),
                            prop.get("lng"),
                            prop.get("infra_score", 0),
                            prop.get("time_info", ""),
                            prop.get("total_score", 0)
                        ))
            
            conn.commit()
            print(f"사용자 {self.user_uuid}의 추천 결과 저장 완료")
            
        except Exception as e:
            print(f"추천 결과 저장 오류: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

def main():
    """메인 함수 - 채팅봇 테스트용"""
    # 테스트용 사용자 ID
    user_uuid = "test_user_123"
    
    # 채팅봇 인스턴스 생성
    chatbot = RealEstateChatbot(user_uuid)
    
    print("부동산 매물 추천 챗봇을 시작합니다. '종료'를 입력하면 대화를 마칩니다.")
    print("안녕하세요! 부동산 매물 추천 AI입니다. 원하시는 조건을 알려주시면 최적의 매물을 추천해드릴게요.")
    print("먼저, 희망하시는 월세는 얼마인가요? (만원 단위)")
    
    # 대화 루프
    while True:
        # 사용자 입력
        user_input = input("\n사용자: ")
        
        # 종료 명령 확인
        if user_input.lower() == '종료':
            print("대화를 종료합니다. 감사합니다!")
            break
        
        # 메시지 처리 및 응답 생성
        response = chatbot.process_message(user_input)
        
        # 응답 출력
        print(f"\n봇: {response}")

if __name__ == "__main__":
    main()