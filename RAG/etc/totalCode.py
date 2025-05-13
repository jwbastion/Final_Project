import os
import math
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from pinecone import Pinecone
from openai import OpenAI
import time

# 환경 변수 로드
load_dotenv()

# OpenAI 및 Pinecone 클라이언트 초기화
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

# 데이터베이스 연결 설정
db_config = {
    'host': os.getenv("DB_HOST", "localhost"),
    'database': os.getenv("DB_NAME", "mydb"),
    'user': os.getenv("DB_USER", "postgres"),
    'password': os.getenv("DB_PASSWORD", "1234"),
    'port': os.getenv("DB_PORT", "5432")
}

# 사용자 상태 관리 클래스
class UserState:
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
            "chat_history": []
        }
    
    def update(self, key, value):
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

# 거리 계산 함수 (하버사인 공식)
def haversine(lat1, lng1, lat2, lng2):
    """두 지점 간의 거리 계산 (미터 단위)"""
    R = 6371000  # 지구 반경 (미터)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# 인프라 데이터 접근 클래스
class InfraDataAccessor:
    def __init__(self, db_config):
        """데이터베이스 연결 설정"""
        self.db_config = db_config
        self.conn = None
        try:
            self.conn = psycopg2.connect(**db_config)
            print("데이터베이스 연결 성공")
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
    
    def __del__(self):
        """소멸자: 연결 종료"""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
    
    def get_infra_data(self, infra_type):
        """인프라 유형에 따라 적절한 테이블에서 데이터 추출"""
        if not self.conn:
            try:
                self.conn = psycopg2.connect(**self.db_config)
                print(f"{infra_type} 데이터베이스 재연결 성공")
            except Exception as e:
                print(f"데이터베이스 재연결 오류: {e}")
                return []
        
        # 각 테이블별 쿼리 매핑
        query_map = {
            "bigmart": """
                SELECT "사업자명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM bigmart
            """,
            "bus": """
                SELECT "정류장명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM bus
            """,
            "cinema": """
                SELECT "사업자명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM cinema
            """,
            "department_store": """
                SELECT "사업자명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM department_store
            """,
            "golf": """
                SELECT "사업자명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM golf
            """,
            "health": """
                SELECT "사업자명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM health
            """,
            "park": """
                SELECT "공원명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM park
            """,
            "pc": """
                SELECT "사업자명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM pc
            """,
            "play": """
                SELECT business_name AS name, longitude, latitude 
                FROM play
            """,
            "police": """
                SELECT "파출소명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM police
            """,
            "post_office": """
                SELECT "사업자명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM post_office
            """,
            "sing": """
                SELECT "사업자명" AS name, "경도" AS longitude, "위도" AS latitude 
                FROM sing
            """,
            "subway": """
                SELECT name, longitude, latitude 
                FROM subway
            """
        }
        
        if infra_type not in query_map:
            print(f"지원되지 않는 인프라 유형: {infra_type}")
            return []
        
        query = query_map[infra_type]
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            print(f"{infra_type} 데이터 {len(results)}개 로드 완료")
            
            # 결과를 표준화된 형식으로 변환
            standardized_results = []
            for row in results:
                # 필드명이 다를 수 있으므로 여러 가능성 체크
                name = row.get("name", "Unknown")
                
                # 위도/경도 필드명 처리
                lat = None
                lng = None
                
                if "latitude" in row:
                    lat = row["latitude"]
                elif "위도" in row:
                    lat = row["위도"]
                
                if "longitude" in row:
                    lng = row["longitude"]
                elif "경도" in row:
                    lng = row["경도"]
                
                # 유효한 위도/경도 값인지 확인
                if lat is not None and lng is not None:
                    try:
                        lat = float(lat)
                        lng = float(lng)
                        
                        standardized_results.append({
                            "name": name,
                            "lat": lat,
                            "lng": lng,
                            "type": infra_type
                        })
                    except (ValueError, TypeError):
                        # 숫자로 변환할 수 없는 경우 스킵
                        continue
            
            print(f"{infra_type} 표준화된 데이터 {len(standardized_results)}개 준비 완료")
            return standardized_results
            
        except Exception as e:
            print(f"쿼리 실행 오류: {e}")
            return []

# 매물 필터링 및 점수 계산 함수
def filter_properties_by_location(properties, user_state):
    """사용자가 선택한 위치 조건을 충족하는 매물 필터링"""
    filtered = []
    lat0 = user_state.get("lat")
    lng0 = user_state.get("lng")
    service = user_state.get("service")
    
    print(f"위치 필터링 시작: 서비스 유형 = {service}, 좌표 = ({lat0}, {lng0})")
    
    if service == "반경":
        radius = user_state.get("radius", 1000)
        print(f"반경 기준 필터링: {radius}m")
        for prop in properties:
            md = prop.metadata
            plat = md.get("lat")
            plng = md.get("lng")
            if plat is None or plng is None:
                continue
            dist = haversine(lat0, lng0, plat, plng)
            if dist <= radius:
                filtered.append(prop)
    elif service == "소요시간":
        time_limit = user_state.get("time_limit", 30)
        movement = user_state.get("movement", "대중교통")
        key = "walk_time" if movement == "도보" else "transit_time"
        print(f"소요시간 기준 필터링: {movement}, 최대 {time_limit}분")
        
        # 가장 가까운 역 3개 찾기
        station_coords = {}
        for prop in properties:
            md = prop.metadata
            st, lat, lng = md.get("station"), md.get("lat"), md.get("lng")
            if st and isinstance(lat, float) and isinstance(lng, float):
                station_coords.setdefault(st, []).append((lat, lng))
        
        print(f"발견된 역 수: {len(station_coords)}")
        
        # 각 역의 평균 좌표 계산
        for st, coords in station_coords.items():
            lats = [c[0] for c in coords]
            lngs = [c[1] for c in coords]
            station_coords[st] = {"lat": sum(lats)/len(lats), "lng": sum(lngs)/len(lngs)}
        
        # 가장 가까운 역 3개 찾기
        dist_list = [(st, haversine(lat0, lng0, c["lat"], c["lng"])) for st, c in station_coords.items()]
        dist_list.sort(key=lambda x: x[1])
        nearest = [st for st, _ in dist_list[:3]]
        
        print(f"가장 가까운 역 3개: {nearest}")
        
        for prop in properties:
            md = prop.metadata
            if md.get("station") in nearest and md.get(key, 9999) <= time_limit:
                filtered.append(prop)
    else:
        # 상관없음
        print("위치 필터링 없음 (상관없음)")
        filtered = properties
    
    print(f"위치 필터링 결과: {len(filtered)}개 매물")
    return filtered

def filter_properties_by_budget(properties, user_state):
    """사용자가 설정한 예산 조건을 충족하는 매물 필터링"""
    rent_limit = user_state.get("rent", 100)
    deposit_limit = user_state.get("deposit", 5000)
    maint_limit = user_state.get("maint", 50)
    
    print(f"예산 필터링 시작: 월세 {rent_limit}만원, 보증금 {deposit_limit}만원, 관리비 {maint_limit}만원")
    
    filtered = []
    for prop in properties:
        md = prop.metadata
        rent = md.get("rent", float("inf"))
        deposit = md.get("deposit", float("inf"))
        maint = md.get("maint", float("inf"))
        
        if rent <= rent_limit and deposit <= deposit_limit and maint <= maint_limit:
            filtered.append(prop)
    
    print(f"예산 필터링 결과: {len(filtered)}개 매물")
    return filtered

def apply_infra_scores(properties, infra_preferences, infra_data):
    """인프라 선호도 반영하여 매물에 점수 부여 (단순화된 버전)"""
    # 우선순위에 따라 정렬 (가중치 내림차순)
    sorted_infra = sorted(infra_preferences.items(), key=lambda x: x[1], reverse=True)
    
    print(f"인프라 점수 계산 시작: {len(properties)}개 매물, {len(sorted_infra)}개 인프라 유형")
    
    # 각 매물에 점수 초기화
    scored_properties = []
    
    for prop in properties:
        md = prop.metadata
        prop_info = {
            "address": md.get("address", "주소 정보 없음"),
            "station": md.get("station", "역 정보 없음"),
            "rent": md.get("rent", 0),
            "deposit": md.get("deposit", 0),
            "maint": md.get("maint", 0),
            "lat": md.get("lat"),
            "lng": md.get("lng"),
            "walk_time": md.get("walk_time"),
            "transit_time": md.get("transit_time"),
            "infra_score": 0,
            "infra_details": {}
        }
        
        if prop_info["lat"] is None or prop_info["lng"] is None:
            scored_properties.append(prop_info)
            continue
        
        plat = prop_info["lat"]
        plng = prop_info["lng"]
        
        # 각 인프라 유형별로 점수 계산
        for infra_type, weight in sorted_infra:
            # 해당 인프라 데이터 필터링
            infra_items = [item for item in infra_data if item["type"] == infra_type]
            
            if not infra_items:
                print(f"경고: {infra_type} 유형의 인프라 데이터가 없습니다.")
                continue
                
            # 가장 가까운 인프라 시설 거리 계산
            min_dist = float("inf")
            nearest_name = None
            
            for item in infra_items:
                dist = haversine(plat, plng, item["lat"], item["lng"])
                if dist < min_dist:
                    min_dist = dist
                    nearest_name = item["name"]
            
            # 단순 거리 기반 점수 계산 (500m 기준)
            threshold = 500  # 기준 거리 (미터)
            if min_dist <= threshold:
                score = weight  # 가중치만큼 점수 부여
            else:
                score = -weight  # 멀면 가중치만큼 감점
            
            # 점수 누적
            prop_info["infra_score"] += score
            prop_info["infra_details"][infra_type] = {
                "distance": min_dist,
                "score": score,
                "nearest": nearest_name
            }
        
        scored_properties.append(prop_info)
    
    # 인프라 점수로 매물 정렬
    scored_properties.sort(key=lambda x: x.get("infra_score", 0), reverse=True)
    print(f"인프라 점수 계산 완료: {len(scored_properties)}개 매물 점수화")
    return scored_properties

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

# RAG 검색 및 추천 클래스
class RealEstateRecommender:
    def __init__(self, index, user_state):
        self.index = index
        self.user_state = user_state
        self.data_accessor = InfraDataAccessor(db_config)
        self.recursion_depth = 0  # 재귀 호출 깊이 제한
    
    def search_properties(self):
        """Pinecone에서 매물 검색"""
        try:
            print("Pinecone에서 매물 검색 시작")
            resp = self.index.query(vector=[0.0]*1536, top_k=500, include_metadata=True)
            print(f"Pinecone 검색 결과: {len(resp.matches)}개 매물")
            return resp.matches
        except Exception as e:
            print(f"Pinecone 검색 오류: {e}")
            # 오류 발생 시 빈 리스트 반환
            return []
    
    def get_all_infra_data(self):
        """모든 인프라 데이터 로드"""
        infra_data = []
        preferences = self.user_state.get("infra_preferences", {})
        
        if not preferences:
            print("경고: 인프라 선호도 설정이 없습니다.")
            return []
            
        print(f"인프라 데이터 로드 시작: {len(preferences)}개 유형")
        
        for infra_type in preferences.keys():
            type_data = self.data_accessor.get_infra_data(infra_type)
            infra_data.extend(type_data)
        
        print(f"전체 인프라 데이터 로드 완료: {len(infra_data)}개 항목")
        return infra_data
    
    def get_recommendations(self, is_retry=False):
        """추천 매물 검색 및 필터링"""
        # 재귀 호출 깊이 제한
        self.recursion_depth += 1
        if self.recursion_depth > 2:  # 최대 2번까지만 재시도
            print("최대 재시도 횟수 초과")
            self.recursion_depth = 0
            return {"location_based": [], "budget_based": [], "combined": []}
        
        # 모든 매물 검색
        all_properties = self.search_properties()
        print(f"검색된 전체 매물 수: {len(all_properties)}")
        
        if not all_properties:
            print("검색된 매물이 없습니다. 기본 매물을 반환합니다.")
            return self.get_default_recommendations()
        
        # 1. 위치 기반 필터링
        location_filtered = filter_properties_by_location(all_properties, self.user_state)
        print(f"위치 조건 충족 매물 수: {len(location_filtered)}")
        
        # 2. 예산 기반 필터링
        budget_filtered = filter_properties_by_budget(all_properties, self.user_state)
        print(f"예산 조건 충족 매물 수: {len(budget_filtered)}")
        
        # 3. 종합 추천 (위치 + 예산 조건 모두 충족)
        combined_filtered = []
        
        try:
            location_ids = {getattr(prop, 'id', None) for prop in location_filtered}
            
            for prop in budget_filtered:
                if getattr(prop, 'id', None) in location_ids:
                    combined_filtered.append(prop)
            
            print(f"종합 조건 충족 매물 수: {len(combined_filtered)}")
        except Exception as e:
            print(f"종합 매물 필터링 오류: {e}")
        
        # 인프라 데이터 로드
        infra_data = self.get_all_infra_data()
        
        if not infra_data and self.user_state.get("infra_preferences"):
            print("인프라 데이터를 로드할 수 없습니다.")
        
        # 4. 인프라 점수 적용
        try:
            location_scored = apply_infra_scores(
                location_filtered, 
                self.user_state.get("infra_preferences", {}), 
                infra_data
            )
            
            budget_scored = apply_infra_scores(
                budget_filtered, 
                self.user_state.get("infra_preferences", {}), 
                infra_data
            )
            
            combined_scored = apply_infra_scores(
                combined_filtered,
                self.user_state.get("infra_preferences", {}),
                infra_data
            )
        except Exception as e:
            print(f"인프라 점수 계산 오류: {e}")
            location_scored = []
            budget_scored = []
            combined_scored = []
        
        # 이동 시간 정보 추가
        movement = self.user_state.get("movement", "상관없음")
        for prop in location_scored:
            prop["time_info"] = format_time_info(prop, movement)
        
        for prop in budget_scored:
            prop["time_info"] = format_time_info(prop, movement)
            
        for prop in combined_scored:
            prop["time_info"] = format_time_info(prop, movement)
        
        # 결과가 없을 경우 조건 완화 후 재검색
        if (not location_scored or not budget_scored or not combined_scored) and not is_retry:
            print("조건에 맞는 매물이 부족하여 검색 조건을 완화합니다...")
            
            # 반경 확장 (원래 반경의 2배)
            if self.user_state.get("service") == "반경":
                original_radius = self.user_state.get("radius", 500)
                new_radius = original_radius * 2
                self.user_state.update("radius", new_radius)
                print(f"검색 반경을 {original_radius}m에서 {new_radius}m로 확장합니다.")
            
            # 예산 범위 확장 (20% 증가)
            original_rent = self.user_state.get("rent", 50)
            new_rent = int(original_rent * 1.2)
            self.user_state.update("rent", new_rent)
            print(f"월세 범위를 {original_rent}만원에서 {new_rent}만원으로 확장합니다.")
            
            # 재검색
            return self.get_recommendations(is_retry=True)
        
        # 재귀 깊이 초기화
        self.recursion_depth = 0
        
        return {
            "location_based": location_scored[:5],  # 상위 5개만 반환
            "budget_based": budget_scored[:5],      # 상위 5개만 반환
            "combined": combined_scored[:5]         # 상위 5개만 반환
        }
    
    def get_default_recommendations(self):
        """기본 추천 매물 (검색 결과가 없을 때 사용)"""
        print("기본 추천 매물 반환")
        
        # 기본 매물 정보
        default_properties = [
            {
                "address": "서울 강남구 역삼동 123-45",
                "station": "강남역",
                "rent": 45,
                "deposit": 500,
                "maint": 10,
                "time_info": "도보 5분",
                "infra_score": 8.5,
                "infra_details": {
                    "subway": {"distance": 350, "score": 5, "nearest": "강남역"},
                    "park": {"distance": 450, "score": 2.5, "nearest": "역삼공원"},
                    "health": {"distance": 200, "score": 1, "nearest": "역삼헬스센터"}
                }
            },
            {
                "address": "서울 마포구 합정동 456-78",
                "station": "합정역",
                "rent": 40,
                "deposit": 300,
                "maint": 8,
                "time_info": "도보 7분",
                "infra_score": 7.8,
                "infra_details": {
                    "subway": {"distance": 400, "score": 4.5, "nearest": "합정역"},
                    "park": {"distance": 350, "score": 3, "nearest": "망원한강공원"},
                    "health": {"distance": 500, "score": 0.3, "nearest": "마포헬스클럽"}
                }
            }
        ]
        
        return {
            "location_based": default_properties,
            "budget_based": default_properties,
            "combined": default_properties
        }

# LLM 처리 클래스
class LLMProcessor:
    def __init__(self, client):
        self.client = client
    
    def generate_response(self, user_message, context, chat_history):
        """LLM을 사용하여 응답 생성"""
        # 대화 이력 및 컨텍스트 포맷팅
        history_text = ""
        for entry in chat_history:
            history_text += f"사용자: {entry['user']}\n봇: {entry['bot']}\n\n"
        
        # 컨텍스트 포맷팅
        context_text = ""
        if context.get("location_based"):
            context_text += "위치 기반 추천 매물:\n"
            for i, prop in enumerate(context["location_based"], 1):
                infra_score = prop.get("infra_score", 0)
                context_text += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                
                # 인프라 세부 정보 추가
                if prop.get("infra_details"):
                    context_text += "  인프라 세부 정보:\n"
                    for infra_type, detail in prop["infra_details"].items():
                        if detail.get("score", 0) > 0:
                            context_text += f"    - {infra_type}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
        
        if context.get("budget_based"):
            context_text += "\n예산 기반 추천 매물:\n"
            for i, prop in enumerate(context["budget_based"], 1):
                infra_score = prop.get("infra_score", 0)
                context_text += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                
                # 인프라 세부 정보 추가
                if prop.get("infra_details"):
                    context_text += "  인프라 세부 정보:\n"
                    for infra_type, detail in prop["infra_details"].items():
                        if detail.get("score", 0) > 0:
                            context_text += f"    - {infra_type}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
        
        if context.get("combined"):
            context_text += "\n종합 추천 매물 (위치+예산+인프라):\n"
            for i, prop in enumerate(context["combined"], 1):
                infra_score = prop.get("infra_score", 0)
                context_text += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                
                # 인프라 세부 정보 추가
                if prop.get("infra_details"):
                    context_text += "  인프라 세부 정보:\n"
                    for infra_type, detail in prop["infra_details"].items():
                        if detail.get("score", 0) > 0:
                            context_text += f"    - {infra_type}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
        
        # 추천 매물이 없는 경우
        if not context.get("location_based") and not context.get("budget_based") and not context.get("combined"):
            context_text = "현재 설정하신 조건에 맞는 매물을 찾지 못했습니다. 다음과 같이 조건을 변경해보세요:\n"
            context_text += "1. 예산 범위를 넓혀보세요 (월세, 보증금 상향 조정)\n"
            context_text += "2. 검색 반경을 넓혀보세요 (현재 반경 → 더 넓은 범위)\n"
            context_text += "3. 다른 지역도 고려해보세요\n"
        
        # LLM 프롬프트 구성
        prompt = f"""당신은 부동산 매물 추천 AI 챗봇입니다. 사용자의 위치, 예산, 이동 방식, 인프라 선호도 등을 고려하여 최적의 매물을 추천해주세요.

대화 이력:
{history_text}

추천 매물 정보:
{context_text}

사용자 메시지: {user_message}

친절하고 도움이 되는 응답을 제공해주세요. 사용자가 특정 매물에 관심을 보이면 더 자세한 정보를 제공하고, 
추가 질문이 있으면 답변해주세요. 매물이 없는 경우에는 검색 조건을 변경해보라고 제안해주세요.
"""

        try:
            # LLM 호출
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # 또는 사용 가능한 모델
                messages=[{"role": "system", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM 응답 생성 오류: {e}")
            return "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다. 다시 시도해주세요."

# 챗봇 클래스
class RealEstateChatbot:
    def __init__(self):
        self.user_state = UserState()
        self.recommender = RealEstateRecommender(index, self.user_state)
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

# 챗봇 실행
def main():
    print("🏠 부동산 매물 추천 챗봇을 시작합니다.")
    print("원하시는 조건을 알려주시면 최적의 매물을 추천해드립니다.")
    
    chatbot = RealEstateChatbot()
    
    # 예산 관련 변수
    budget_names = {'rent': '월세', 'deposit': '보증금', 'maint': '관리비'}
    current_key = 'rent'
    cur = chatbot.user_state.get(current_key)
    
    # 첫 질문 출력 (사용자 입력 없이)
    print(f"\n🤖 챗봇: 현재 설정하신 {budget_names[current_key]}은 최대 {cur}만원이에요. 더 높이거나 낮추고 싶다면 금액을 입력해주세요. (없으면 '없음')")
    
    # 대화 상태 변수
    setup_stage = "budget"  # 초기 단계: 예산 설정
    
    # 인프라 유형 및 설명
    infra_types = [
        {"code": "subway", "name": "지하철역", "description": "대중교통 접근성"},
        {"code": "bus", "name": "버스정류장", "description": "버스 노선 접근성"},
        {"code": "bigmart", "name": "대형마트", "description": "쇼핑 및 생필품 구매"},
        {"code": "department_store", "name": "백화점", "description": "쇼핑 및 편의시설"},
        {"code": "park", "name": "공원", "description": "여가 및 산책 공간"},
        {"code": "health", "name": "헬스장/의료시설", "description": "건강 및 의료 서비스"},
        {"code": "cinema", "name": "영화관", "description": "문화 및 엔터테인먼트"},
        {"code": "golf", "name": "골프장", "description": "스포츠 및 레저"},
        {"code": "pc", "name": "PC방", "description": "게임 및 인터넷"},
        {"code": "play", "name": "놀이시설", "description": "오락 및 여가"},
        {"code": "police", "name": "경찰서", "description": "치안 및 안전"},
        {"code": "post_office", "name": "우체국", "description": "우편 및 행정 서비스"},
        {"code": "sing", "name": "노래방", "description": "엔터테인먼트"}
    ]
    
    # 사용자 인프라 선호도 저장
    user_infra_preferences = {}
    
    while True:
        user_input = input("\n🙋 사용자: ")
        if user_input.lower() in ['종료', '끝', 'exit', 'quit']:
            print("챗봇을 종료합니다. 감사합니다!")
            break
        
        # 예산 설정 단계
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
                
                # 예산 설정 완료 후 거주지 선호도 질문
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
                    for i, infra in enumerate(infra_types, 1):
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
                    chatbot.user_state.update("time_limit", 15)  # 기본값
                
                setup_stage = "infra"  # 인프라 선호도 조사로 넘어감
                print("\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.")
                for i, infra in enumerate(infra_types, 1):
                    print(f"{i}. {infra['name']} - {infra['description']}")
                print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")
            
            elif current_key == 'radius':
                try:
                    radius = int(''.join(filter(str.isdigit, user_input)))
                    chatbot.user_state.update("radius", radius)
                except:
                    chatbot.user_state.update("radius", 500)  # 기본값
                
                setup_stage = "infra"  # 인프라 선호도 조사로 넘어감
                print("\n🤖 챗봇: 다음 중에서 가장 중요하게 생각하는 인프라를 최소 1개, 최대 3개까지 선택해주세요.")
                for i, infra in enumerate(infra_types, 1):
                    print(f"{i}. {infra['name']} - {infra['description']}")
                print("\n번호를 입력해주세요 (예: 1,3,5 또는 1 3 5)")
        
        # 인프라 선호도 설정 단계 (최소 1개, 최대 3개 선택 방식)
        elif setup_stage == "infra":
            try:
                # 쉼표나 공백으로 구분된 입력 처리
                if ',' in user_input:
                    selections = [int(s.strip()) for s in user_input.split(',')]
                else:
                    selections = [int(s.strip()) for s in user_input.split()]
                
                # 선택 검증
                if not selections or len(selections) > 3 or not all(1 <= s <= len(infra_types) for s in selections):
                    print(f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(infra_types)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)")
                    continue
                
                # 선택한 인프라 저장 (가중치: 1순위=5, 2순위=3, 3순위=1)
                weights = [5, 3, 1]
                for i, selection in enumerate(selections):
                    if i < len(weights):  # 최대 3개까지만 처리
                        infra_type = infra_types[selection-1]["code"]
                        user_infra_preferences[infra_type] = weights[i]
                
                print(f"선택한 인프라: {user_infra_preferences}")
                
                # 모든 인프라 질문 완료
                setup_stage = "complete"
                chatbot.user_state.update("infra_preferences", user_infra_preferences)
                chatbot.setup_complete = True
                
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
                        if recommendations["location_based"]:
                            result += "**위치 기반 추천 매물**\n"
                            for i, prop in enumerate(recommendations["location_based"], 1):
                                infra_score = prop.get("infra_score", 0)
                                result += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                                
                                # 인프라 세부 정보 추가
                                if prop.get("infra_details"):
                                    result += "   인프라 세부 정보:\n"
                                    for infra_type, detail in prop["infra_details"].items():
                                        if detail.get("score", 0) > 0:
                                            infra_name = next((x["name"] for x in infra_types if x["code"] == infra_type), infra_type)
                                            result += f"   - {infra_name}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
                        
                        if recommendations["budget_based"]:
                            result += "\n**예산 기반 추천 매물**\n"
                            for i, prop in enumerate(recommendations["budget_based"], 1):
                                infra_score = prop.get("infra_score", 0)
                                result += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                                
                                # 인프라 세부 정보 추가
                                if prop.get("infra_details"):
                                    result += "   인프라 세부 정보:\n"
                                    for infra_type, detail in prop["infra_details"].items():
                                        if detail.get("score", 0) > 0:
                                            infra_name = next((x["name"] for x in infra_types if x["code"] == infra_type), infra_type)
                                            result += f"   - {infra_name}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
                        
                        if recommendations["combined"]:
                            result += "\n**종합 추천 매물 (위치+예산+인프라)**\n"
                            for i, prop in enumerate(recommendations["combined"], 1):
                                infra_score = prop.get("infra_score", 0)
                                result += f"{i}. {prop['address']} ({prop['station']}) - 월세 {prop['rent']}만원, 보증금 {prop['deposit']}만원, 관리비 {prop['maint']}만원, {prop['time_info']}, 인프라 점수: {infra_score:.1f}\n"
                                
                                # 인프라 세부 정보 추가
                                if prop.get("infra_details"):
                                    result += "   인프라 세부 정보:\n"
                                    for infra_type, detail in prop["infra_details"].items():
                                        if detail.get("score", 0) > 0:
                                            infra_name = next((x["name"] for x in infra_types if x["code"] == infra_type), infra_type)
                                            result += f"   - {infra_name}: {detail['nearest']} (거리: {detail['distance']:.0f}m)\n"
                        
                        result += "\n이 중에서 어떤 매물이 마음에 드시나요? 또는 다른 조건으로 검색하고 싶으신가요?"
                    
                    print(f"\n🤖 챗봇: {result}")
                
                except Exception as e:
                    print(f"\n🤖 챗봇: 추천 매물을 가져오는 중 오류가 발생했습니다: {e}")
                    print("\n🤖 챗봇: 죄송합니다. 매물 검색 중 문제가 발생했습니다. 다시 시도해주시거나 다른 조건으로 검색해보세요.")
            
            except ValueError:
                print(f"\n🤖 챗봇: 선택이 올바르지 않습니다. 1부터 {len(infra_types)}까지의 숫자 중 최소 1개, 최대 3개를 선택해주세요. (예: 1,3,5)")
        
        # 설정 완료 후 일반 대화
        elif setup_stage == "complete":
            response = chatbot.process_message(user_input)
            print(f"\n🤖 챗봇: {response}")

if __name__ == "__main__":
    main()
