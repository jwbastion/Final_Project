import psycopg2
from psycopg2.extras import RealDictCursor
from utils import haversine, format_time_info
from config import DB_CONFIG, INFRA_TYPES

class InfraDataAccessor:
    def __init__(self, db_config):
        """데이터베이스 연결 설정"""
        self.db_config = db_config
        self.conn = None
        self.use_db = True  # 데이터베이스 사용 여부
        try:
            self.conn = psycopg2.connect(**db_config)
            print("데이터베이스 연결 성공")
        except Exception as e:
            print(f"데이터베이스 연결 오류: {e}")
            self.use_db = False
        
        # 테이블이 없을 경우 사용할 가상 데이터
        self.virtual_data = self._create_virtual_data()
    
    def _create_virtual_data(self):
        """데이터베이스 연결 실패 시 사용할 가상 데이터"""
        # 서울 주요 역의 좌표 (예시)
        subway_stations = [
            {"name": "강남역", "lat": 37.498163, "lng": 127.027724, "type": "traffic_subway"},
            {"name": "신논현역", "lat": 37.504478, "lng": 127.025030, "type": "traffic_subway"},
            {"name": "홍대입구역", "lat": 37.557527, "lng": 126.924191, "type": "traffic_subway"},
            {"name": "여의도역", "lat": 37.521624, "lng": 126.924191, "type": "traffic_subway"},
            {"name": "합정역", "lat": 37.549463, "lng": 126.914019, "type": "traffic_subway"},
            # 강북구 역 추가 (실제 DB의 좌표값 사용)
            {"name": "수유(강북구청)역", "lat": 37.6401291, "lng": 127.027782, "type": "traffic_subway"},
            {"name": "가오리역", "lat": 37.6416447, "lng": 127.016758, "type": "traffic_subway"},
            {"name": "화계역", "lat": 37.6335358, "lng": 127.017527, "type": "traffic_subway"},
            {"name": "미아역", "lat": 37.627264, "lng": 127.025666, "type": "traffic_subway"},
            {"name": "미아사거리역", "lat": 37.613292, "lng": 127.030053, "type": "traffic_subway"}
        ]
        
        # 주요 마트
        marts = [
            {"name": "이마트 강남점", "lat": 37.498700, "lng": 127.028512, "type": "life_mart"},
            {"name": "홈플러스 합정점", "lat": 37.550023, "lng": 126.915264, "type": "life_mart"}
        ]
        
        # 주요 공원
        parks = [
            {"name": "한강공원", "lat": 37.513222, "lng": 126.943624, "type": "life_park"},
            {"name": "올림픽공원", "lat": 37.520509, "lng": 127.121931, "type": "life_park"}
        ]
        
        # 가상 데이터 병합
        return {
            "traffic_subway": subway_stations,
            "life_mart": marts,
            "life_park": parks
        }
    
    def __del__(self):
        """소멸자: 연결 종료"""
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
    
    def get_infra_data(self, infra_type):
        """인프라 유형에 따라 적절한 테이블에서 데이터 추출 또는 가상 데이터 반환"""
        # 먼저 DB에서 데이터 가져오기 시도
        try:
            if not self.conn or self.conn.closed:
                self.conn = psycopg2.connect(**self.db_config)
                print(f"{infra_type} - 데이터베이스 재연결 성공")
            
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # 테이블 존재 여부 확인
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{infra_type}'
                );
            """)
            
            table_exists = cursor.fetchone()['exists']
            
            if not table_exists:
                print(f"{infra_type} 테이블이 존재하지 않습니다. 가상 데이터를 사용합니다.")
                cursor.close()
                return self.virtual_data.get(infra_type, [])
            
            # 테이블 구조 확인 (필드명 파악)
            cursor.execute(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{infra_type}'
            """)
            
            columns = [row['column_name'] for row in cursor.fetchall()]
            
            # 필드명에 따라 쿼리 구성
            name_field = "business_name" if "business_name" in columns else "name"
            lat_field = "latitude" if "latitude" in columns else "lat"
            lng_field = "longitude" if "longitude" in columns else "lng"
            
            # 실제 데이터 조회
            query = f"""
                SELECT {name_field} AS name, {lng_field} AS lng, {lat_field} AS lat
                FROM {infra_type}
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            
            # 결과 표준화
            standardized_results = []
            for row in results:
                if row.get("name") and row.get("lat") is not None and row.get("lng") is not None:
                    try:
                        standardized_results.append({
                            "name": row["name"],
                            "lat": float(row["lat"]),
                            "lng": float(row["lng"]),
                            "type": infra_type
                        })
                    except (ValueError, TypeError):
                        # 숫자로 변환할 수 없는 경우 스킵
                        continue
            
            print(f"{infra_type} 데이터 {len(standardized_results)}개 로드 완료")
            
            if standardized_results:
                return standardized_results
            
            # 결과가 없으면 가상 데이터 반환
            print(f"{infra_type} 데이터가 없습니다. 가상 데이터를 사용합니다.")
            return self.virtual_data.get(infra_type, [])
            
        except Exception as e:
            print(f"{infra_type} 데이터 조회 오류: {e}")
            return self.virtual_data.get(infra_type, [])


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

def filter_properties_by_extended_budget(properties, user_state, multiplier=1.3):
    """확장된 예산 범위로 매물 필터링 (예산 조건 완화)"""
    rent_limit = user_state.get("rent", 100) * multiplier
    deposit_limit = user_state.get("deposit", 5000) * multiplier
    maint_limit = user_state.get("maint", 50) * multiplier
    
    print(f"확장 예산 필터링: 월세 {rent_limit:.0f}만원, 보증금 {deposit_limit:.0f}만원, 관리비 {maint_limit:.0f}만원")
    
    filtered = []
    for prop in properties:
        md = prop.metadata
        rent = md.get("rent", float("inf"))
        deposit = md.get("deposit", float("inf"))
        maint = md.get("maint", float("inf"))
        
        if rent <= rent_limit and deposit <= deposit_limit and maint <= maint_limit:
            filtered.append(prop)
    
    print(f"확장 예산 필터링 결과: {len(filtered)}개 매물")
    return filtered

def filter_properties_by_features(properties, user_state):
    """사용자가 선호하는 매물 특성을 충족하는 매물 필터링 (소프트 스코어링 적용)"""
    feature_preferences = user_state.get("property_features", {})
    if not feature_preferences:
        print("매물 특성 필터링: 설정된 선호 조건 없음")
        return properties, []
    
    print("매물 특성 필터링 시작: ", feature_preferences)
    
    filtered = []
    filtering_results = []  # 필터링 이유 추적
    
    for prop in properties:
        md = prop.metadata
        
        # 필터링 통과 여부 플래그
        passes_filters = True
        filter_reason = None
        
        # 층수 필터링 (간소화된 버전)
        floor_pref = feature_preferences.get("floor", "").lower()
        floor_str = md.get("floor", "").lower()
        
        # 반지하 제외 조건
        if "반지하 제외" in floor_pref and ("반지" in floor_str or "지하" in floor_str):
            filter_reason = f"{md.get('address')} - 반지하 제외 조건으로 제외"
            passes_filters = False
            
        # 그외 층수 필터링 (저층, 중층, 고층)
        try:
            if passes_filters:
                floor_num = int(''.join(filter(str.isdigit, floor_str)))
                
                if "저층" in floor_pref and (floor_num > 3 or floor_num == 0):
                    filter_reason = f"{md.get('address')} - 저층이 아니라서 제외"
                    passes_filters = False
                elif "중층" in floor_pref and (floor_num < 4 or floor_num > 7):
                    filter_reason = f"{md.get('address')} - 중층이 아니라서 제외"
                    passes_filters = False
                elif "고층" in floor_pref and floor_num < 8:
                    filter_reason = f"{md.get('address')} - 고층이 아니라서 제외"
                    passes_filters = False
        except:
            # 층수를 숫자로 변환할 수 없는 경우
            pass
        
        # 면적 필터링
        if passes_filters:
            size_pref = feature_preferences.get("size", "").lower()
            size = md.get("size", 0)
            
            try:
                # 문자열로 저장된 경우 숫자로 변환
                if isinstance(size, str) and size.strip():
                    size = float(''.join(c for c in size if c.isdigit() or c == '.'))
                
                # 사용자 선호도에 따른 필터링
                if "5평 이하" in size_pref and size > 5:
                    filter_reason = f"{md.get('address')} - 5평 이하가 아니라서 제외"
                    passes_filters = False
                elif "5~10평" in size_pref and (size < 5 or size > 10):
                    filter_reason = f"{md.get('address')} - 5~10평 범위가 아니라서 제외"
                    passes_filters = False
                elif "10~15평" in size_pref and (size < 10 or size > 15):
                    filter_reason = f"{md.get('address')} - 10~15평 범위가 아니라서 제외"
                    passes_filters = False
                elif "15~20평" in size_pref and (size < 15 or size > 20):
                    filter_reason = f"{md.get('address')} - 15~20평 범위가 아니라서 제외"
                    passes_filters = False
                elif "20평 이상" in size_pref and size < 20:
                    filter_reason = f"{md.get('address')} - 20평 이상이 아니라서 제외"
                    passes_filters = False
            except (ValueError, TypeError):
                # 면적 데이터 오류 시 필터링 스킵
                pass
        
        # 향 필터링 (남향 등)
        if passes_filters:
            direction_pref = feature_preferences.get("direction", "").lower()
            direction = md.get("direction", md.get("조망", "")).lower()
            
            if direction_pref and direction_pref != "상관없음":
                # 각 방향 확인
                if "남향" in direction_pref and "남" not in direction:
                    filter_reason = f"{md.get('address')} - 남향이 아니라서 제외"
                    passes_filters = False
                elif "동향" in direction_pref and "동" not in direction:
                    filter_reason = f"{md.get('address')} - 동향이 아니라서 제외"
                    passes_filters = False
                elif "서향" in direction_pref and "서" not in direction:
                    filter_reason = f"{md.get('address')} - 서향이 아니라서 제외"
                    passes_filters = False
                elif "북향" in direction_pref and "북" not in direction:
                    filter_reason = f"{md.get('address')} - 북향이 아니라서 제외"
                    passes_filters = False
        
        # 난방 방식 필터링
        if passes_filters:
            heating_pref = feature_preferences.get("heating", "").lower()
            heating = str(md.get("heating_type", md.get("난방", ""))).lower()
            
            if heating_pref and heating_pref != "상관없음":
                if "개별난방" in heating_pref and "개별" not in heating:
                    filter_reason = f"{md.get('address')} - 개별난방이 아니라서 제외"
                    passes_filters = False
                elif "중앙난방" in heating_pref and "중앙" not in heating:
                    filter_reason = f"{md.get('address')} - 중앙난방이 아니라서 제외"
                    passes_filters = False
                elif "지역난방" in heating_pref and "지역" not in heating:
                    filter_reason = f"{md.get('address')} - 지역난방이 아니라서 제외"
                    passes_filters = False
        
        # 주차 및 엘리베이터는 더 이상 하드 필터링하지 않음 (소프트 스코어로 변경)
        # 이 부분이 기존 코드에서 삭제된 부분
        
        # 모든 조건 통과 시 추가
        if passes_filters:
            filtered.append(prop)
        elif filter_reason:
            # 필터링 이유 추적
            filtering_results.append(f"⚠️ 추가 필터링: {filter_reason}")
            print(f"⚠️ 추가 필터링: {filter_reason}")
    
    print(f"매물 특성 필터링 결과: {len(filtered)}개 매물 (원래: {len(properties)}개)")
    
    # 필터링 결과가 없는 경우 사용자에게 추천 사항 제공
    if len(filtered) == 0 and filtering_results:
        # 어떤 조건이 가장 많이 필터링 원인이 되었는지 분석
        floor_count = sum(1 for result in filtering_results if "층" in result)
        direction_count = sum(1 for result in filtering_results if "향" in result)
        
        # 가장 많은 필터링 원인 식별
        filter_counts = {
            "층수": floor_count,
            "방향": direction_count
        }
        
        # 가장 많은 필터링 원인 출력
        max_filter = max(filter_counts.items(), key=lambda x: x[1])
        if max_filter[1] > 0:
            print(f"\n🔍 분석 결과: 가장 많은 매물이 '{max_filter[0]}' 조건으로 필터링되었습니다.")
            print("💡 추천 사항: 이 조건을 '상관없음'으로 변경하면 더 많은 매물을 볼 수 있습니다.")
    
    return filtered, filtering_results

def apply_infra_scores(properties, infra_preferences, infra_data):
    """인프라 선호도 반영하여 매물에 점수 부여 (소프트 스코어링 적용)"""
    # 우선순위에 따라 정렬 (가중치 내림차순)
    sorted_infra = sorted(infra_preferences.items(), key=lambda x: x[1], reverse=True)
    
    print(f"인프라 점수 계산 시작: {len(properties)}개 매물, {len(sorted_infra)}개 인프라 유형")
    
    # 각 매물에 점수 초기화
    scored_properties = []
    
    for prop in properties:
        # metadata에서 필요한 정보 추출
        md = prop.metadata if hasattr(prop, 'metadata') else prop
        
        # 기본 정보 설정 - Pinecone 데이터 구조에 맞게 수정
        prop_info = {
            "address": md.get("address", "주소 정보 없음"),
            "station": md.get("station", "역 정보 없음"),
            "rent": md.get("rent", 0),
            "deposit": md.get("deposit", 0),
            "maint": md.get("maint", 0),
            "lat": md.get("lat"),
            "lng": md.get("lng"),
            "walk_time": md.get("walk_time"),
            "transit_time": md.get("transit_time", md.get("subway_time")),
            "floor": md.get("floor", md.get("층수", "층수 정보 없음")),
            "heating_type": md.get("난방", md.get("heating_type", "난방 정보 없음")),
            "parking": "있음" in str(md.get("주차", md.get("parking", ""))),
            "facilities": md.get("생활시설", md.get("facilities", "시설 정보 없음")),
            "view": md.get("조망", md.get("direction", md.get("view", "조망 정보 없음"))),
            "size": md.get("size", 0),  # 면적 추가
            "엘리베이터": md.get("엘리베이터", "정보 없음"),  # 엘리베이터 정보 추가
            "type": md.get("type", "원룸"),  # 매물 유형 추가
            "안전시설": md.get("안전시설", "정보 없음"),  # 안전시설 정보 추가
            "infra_score": 0,
            "feature_score": 0,  # 새로 추가: 특성 점수
            "total_score": 0,    # 새로 추가: 총 점수
            "infra_details": {},
            "id": getattr(prop, 'id', None)  # ID 보존
        }
        
        if prop_info["lat"] is None or prop_info["lng"] is None:
            scored_properties.append(prop_info)
            continue
        
        # 좌표 가져오기
        plat = float(prop_info["lat"])
        plng = float(prop_info["lng"])
        
        # 총 인프라 점수 계산 (기본값 설정)
        total_score = 0
        
        # 각 인프라 유형별로 점수 계산
        for infra_type, weight in sorted_infra:
            # 해당 인프라 데이터 필터링
            infra_items = [item for item in infra_data if item["type"] == infra_type]
            
            if not infra_items:
                print(f"경고: {infra_type} 유형의 인프라 데이터가 없습니다.")
                continue
            
            # 매물의 역 정보를 활용 (지하철역의 경우)
            station_name = prop_info.get("station", "")
            if station_name and infra_type == "traffic_subway":
                # 동일한 역 이름을 가진 항목 우선 검색
                matched_stations = [item for item in infra_items if station_name in item["name"] or item["name"] in station_name]
                
                # 일치하는 역이 있으면 해당 역만 사용
                if matched_stations:
                    infra_items = matched_stations
            
            # 가장 가까운 인프라 시설 거리 계산
            min_dist = float("inf")
            nearest_name = None
            
            for item in infra_items:
                try:
                    item_lat = float(item["lat"])
                    item_lng = float(item["lng"])
                    dist = haversine(plat, plng, item_lat, item_lng)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_name = item["name"]
                except (TypeError, ValueError) as e:
                    print(f"좌표 변환 오류 (무시됨): {e}")
                    continue
            
            # 점수 계산 (거리 기반)
            if nearest_name:
                # 거리 기준 조정: 5km가 넘으면 무시
                if min_dist > 5000:
                    score = 0
                # 1km 이내: 가중치 * (1 - 거리/2000)
                elif min_dist <= 1000:
                    score = weight * (1 - min_dist/2000)
                # 1km 초과: 가중치 * 0.5 * (1 - (거리-1000)/4000)
                else:
                    score = max(0, weight * 0.5 * (1 - (min_dist-1000)/4000))
                
                # 점수 반올림 (소수점 첫째 자리)
                score = round(score, 1)
                
                # 점수가 있는 경우에만 인프라 세부 정보 저장
                if score > 0:
                    prop_info["infra_details"][infra_type] = {
                        "distance": min_dist,
                        "score": score,
                        "nearest": nearest_name
                    }
                
                # 총점에 추가
                total_score += score
        
        # 인프라 점수 저장 (최소 0.5, 최대 5.0)
        prop_info["infra_score"] = min(5.0, max(0.5, total_score)) if total_score > 0 else 0
        
        # 주차 및 엘리베이터 특성에 따른 feature_score 계산 (소프트 스코어 적용)
        feature_score = 0
        
        # 엘리베이터 점수
        elevator_text = str(prop_info.get("엘리베이터", "")).lower()
        if "있" in elevator_text or "가능" in elevator_text:
            feature_score += 1
        
        # 주차 점수
        if prop_info.get("parking"):
            feature_score += 1
        
        # feature_score 저장
        prop_info["feature_score"] = feature_score
        
        # total_score 계산 및 저장 (infra_score + feature_score)
        prop_info["total_score"] = prop_info["infra_score"] + feature_score
        
        # 시간 정보 추가
        if "time_info" not in prop_info or not prop_info["time_info"]:
            prop_info["time_info"] = format_time_info(prop_info, "상관없음")
        
        # 결과 추가
        scored_properties.append(prop_info)
    
    # total_score로 매물 정렬 (중요!)
    scored_properties.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    print(f"인프라 점수 계산 완료: {len(scored_properties)}개 매물 점수화")
    return scored_properties

def get_location_based_properties_with_extended_budget(properties, user_state, lat0, lng0, multiplier=1.3):
    """위치는 만족하지만 예산은 초과하는 매물 중 확장된 예산 범위 내의 매물 찾기"""
    # 확장된 예산 제한
    rent_limit = user_state.get("rent", 100) * multiplier
    deposit_limit = user_state.get("deposit", 5000) * multiplier
    maint_limit = user_state.get("maint", 50) * multiplier
    
    # 서비스 유형 확인 (반경 또는 소요시간)
    service = user_state.get("service")
    
    filtered = []
    
    if service == "반경":
        radius = user_state.get("radius", 1000)
        print(f"위치+확장예산 필터링: 반경 {radius}m, 예산 {rent_limit:.0f}/{deposit_limit:.0f}/{maint_limit:.0f}만원")
        
        for prop in properties:
            md = prop.metadata
            # 예산 체크
            rent = md.get("rent", float("inf"))
            deposit = md.get("deposit", float("inf"))
            maint = md.get("maint", float("inf"))
            
            # 확장된 예산 범위에 포함되는지 확인
            if rent > rent_limit or deposit > deposit_limit or maint > maint_limit:
                continue
                
            # 위치 체크
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
        print(f"위치+확장예산 필터링: {movement} {time_limit}분, 예산 {rent_limit:.0f}/{deposit_limit:.0f}/{maint_limit:.0f}만원")
        
        for prop in properties:
            md = prop.metadata
            # 예산 체크
            rent = md.get("rent", float("inf"))
            deposit = md.get("deposit", float("inf"))
            maint = md.get("maint", float("inf"))
            
            # 확장된 예산 범위에 포함되는지 확인
            if rent > rent_limit or deposit > deposit_limit or maint > maint_limit:
                continue
                
            # 소요시간 체크
            if md.get(key, 9999) <= time_limit:
                filtered.append(prop)
    
    return filtered

class RealEstateRecommender:
    def __init__(self, index, user_state):
        self.index = index
        self.user_state = user_state
        self.data_accessor = InfraDataAccessor(DB_CONFIG)
        self.recursion_depth = 0  # 재귀 호출 깊이 제한
        self.filtering_results = []  # 필터링 결과 추적
    
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
        if self.recursion_depth > 3:  # 최대 3번까지 재시도
            print("최대 재시도 횟수 초과")
            self.recursion_depth = 0
            return {"location_based": [], "budget_based": [], "combined": []}
        
        try:
            # 초기화
            self.filtering_results = []
            
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
            
            # 3. 매물 특성 필터링 (주차, 엘리베이터 제외 - 소프트 스코어링으로 변경)
            feature_filtered, feature_filtering_results = filter_properties_by_features(all_properties, self.user_state)
            print(f"매물 특성 조건 충족 매물 수: {len(feature_filtered)}")
            
            # 필터링 결과 저장
            self.filtering_results.extend(feature_filtering_results)
            
            # 4. 종합 추천 (위치 + 예산 + 특성 조건 모두 충족)
            combined_filtered = []
            
            location_ids = {getattr(prop, 'id', None) for prop in location_filtered}
            budget_ids = {getattr(prop, 'id', None) for prop in budget_filtered}
            feature_ids = {getattr(prop, 'id', None) for prop in feature_filtered}
            
            for prop in all_properties:
                prop_id = getattr(prop, 'id', None)
                if prop_id in location_ids and prop_id in budget_ids and prop_id in feature_ids:
                    combined_filtered.append(prop)
            
            print(f"종합 조건 충족 매물 수: {len(combined_filtered)}")
            
            # 5. 인프라 데이터 로드
            infra_data = self.get_all_infra_data()
            
            if not infra_data and self.user_state.get("infra_preferences"):
                print("인프라 데이터를 로드할 수 없습니다.")
            
            # 6. 인프라 점수 적용 (소프트 스코어링 적용)
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
            
            feature_scored = apply_infra_scores(
                feature_filtered,
                self.user_state.get("infra_preferences", {}),
                infra_data
            )
            
            combined_scored = apply_infra_scores(
                combined_filtered,
                self.user_state.get("infra_preferences", {}),
                infra_data
            )
            
            # 7. 종합 매물이 5개 미만일 경우 조건 완화 처리 (개선된 부분)
            if len(combined_scored) < 5:
                print(f"종합 추천 매물이 {len(combined_scored)}개로 5개 미만입니다. 조건을 완화합니다.")
                
                # 조건 완화 원인 분석 및 안내
                self.provide_recommendation_guidance(location_filtered, budget_filtered, feature_filtered)
                
                # 기존 종합 추천 매물 수 저장
                original_count = len(combined_scored)
                
                # 이미 추가된 매물 ID
                existing_ids = {prop.get("id") for prop in combined_scored}
                
                # 1) 위치 기반 매물 중에서 우선 추가 (위치 우선)
                if len(combined_scored) < 5 and location_scored:
                    print("위치 기반 매물에서 추가...")
                    
                    # 위치 기반 매물 중 중복되지 않는 것만 선택
                    additional_from_location = [
                        prop for prop in location_scored 
                        if prop.get("id") not in existing_ids
                    ]
                    
                    # 필요한 수 계산
                    need_more = 5 - len(combined_scored)
                    added_from_location = 0
                    
                    # 매물 추가
                    for prop in additional_from_location[:need_more]:
                        combined_scored.append(prop)
                        existing_ids.add(prop.get("id"))
                        added_from_location += 1
                    
                    if added_from_location > 0:
                        print(f"위치 기반 매물에서 {added_from_location}개 추가했습니다.")
                
                # 2) 위치 기반 + 확장 예산으로 추가 (위치 유지하면서 예산 완화)
                if len(combined_scored) < 5:
                    print("위치는 유지하면서 예산 범위를 확장하여 매물 검색...")
                    
                    # 위치 + 확장 예산 매물 찾기
                    lat0 = self.user_state.get("lat")
                    lng0 = self.user_state.get("lng")
                    
                    # 위치 만족하면서 예산 확장한 매물 찾기
                    extended_budget_props = get_location_based_properties_with_extended_budget(
                        all_properties,
                        self.user_state,
                        lat0,
                        lng0,
                        multiplier=1.5  # 예산 50% 증가
                    )
                    
                    # 특성 필터링 적용 (옵션)
                    extended_budget_props_filtered, _ = filter_properties_by_features(extended_budget_props, self.user_state)
                    
                    # 인프라 점수 계산
                    extended_scored = apply_infra_scores(
                        extended_budget_props_filtered,
                        self.user_state.get("infra_preferences", {}),
                        infra_data
                    )
                    
                    # 필요한 수 계산
                    need_more = 5 - len(combined_scored)
                    added_from_extended = 0
                    
                    # 이미 추가된 ID 제외하고 추가
                    for prop in extended_scored:
                        if prop.get("id") not in existing_ids and added_from_extended < need_more:
                            combined_scored.append(prop)
                            existing_ids.add(prop.get("id"))
                            added_from_extended += 1
                    
                    if added_from_extended > 0:
                        print(f"위치+확장예산 매물에서 {added_from_extended}개 추가했습니다.")
                
                # 3) 마지막으로 특성 기반 매물 추가 (가능한 위치 근처)
                if len(combined_scored) < 5 and feature_scored:
                    print("매물 특성 기반 매물 중에서 추가 (위치 근접순 정렬)...")
                    
                    # 이미 추가된 ID 제외
                    additional_from_feature = [
                        prop for prop in feature_scored 
                        if prop.get("id") not in existing_ids
                    ]
                    
                    # 위치 기준 정렬 시도 (사용자 위치 정보가 있는 경우)
                    lat0 = self.user_state.get("lat")
                    lng0 = self.user_state.get("lng")
                    if lat0 and lng0:
                        # 거리 계산 후 정렬
                        for prop in additional_from_feature:
                            plat = prop.get("lat")
                            plng = prop.get("lng")
                            if plat and plng:
                                try:
                                    prop["_distance"] = haversine(lat0, lng0, float(plat), float(plng))
                                except:
                                    prop["_distance"] = float("inf")
                            else:
                                prop["_distance"] = float("inf")
                        
                        # 거리순 정렬
                        additional_from_feature.sort(key=lambda x: x.get("_distance", float("inf")))
                        
                        # 임시 거리 필드 제거
                        for prop in additional_from_feature:
                            if "_distance" in prop:
                                del prop["_distance"]
                    
                    # 필요한 수 계산
                    need_more = 5 - len(combined_scored)
                    added_from_feature = 0
                    
                    # 매물 추가
                    for prop in additional_from_feature[:need_more]:
                        combined_scored.append(prop)
                        existing_ids.add(prop.get("id"))
                        added_from_feature += 1
                    
                    if added_from_feature > 0:
                        print(f"매물 특성 기반 매물에서 {added_from_feature}개 추가했습니다.")
                
                # 4) 그래도 부족하면 인프라 점수 높은 매물 추가
                if len(combined_scored) < 5:
                    print("인프라 점수 기반 매물 추가...")
                    
                    # 모든 매물에 인프라 점수 적용
                    all_scored = apply_infra_scores(
                        all_properties,
                        self.user_state.get("infra_preferences", {}),
                        infra_data
                    )
                    
                    # 인프라 점수로 정렬
                    all_scored.sort(key=lambda x: x.get("total_score", 0), reverse=True)  # total_score로 정렬 (변경된 부분)
                    
                    # 이미 추가된 ID 제외
                    additional_from_infra = [
                        prop for prop in all_scored 
                        if prop.get("id") not in existing_ids
                    ]
                    
                    # 필요한 수 계산
                    need_more = 5 - len(combined_scored)
                    added_from_infra = 0
                    
                    # 매물 추가
                    for prop in additional_from_infra[:need_more]:
                        combined_scored.append(prop)
                        added_from_infra += 1
                    
                    if added_from_infra > 0:
                        print(f"인프라 점수 기반 매물에서 {added_from_infra}개 추가했습니다.")
                
                # 최종 추가된 매물 수 출력
                total_added = len(combined_scored) - original_count
                print(f"총 {total_added}개 매물이 조건 완화를 통해 종합 추천에 추가되었습니다.")
                
                # total_score 기준 다시 정렬 (변경된 부분)
                combined_scored.sort(key=lambda x: x.get("total_score", 0), reverse=True)
            
            # 재귀 깊이 초기화
            self.recursion_depth = 0
            
            return {
                "location_based": location_scored[:5],  # 상위 5개만 반환
                "budget_based": budget_scored[:5],      # 상위 5개만 반환
                "feature_based": feature_scored[:5],    # 특성 기반 추천 추가
                "combined": combined_scored[:5],        # 상위 5개만 반환
                "filtering_results": self.filtering_results  # 필터링 결과 추가
            }
        except Exception as e:
            print(f"추천 매물 가져오기 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return self.get_default_recommendations()
    
    def provide_recommendation_guidance(self, location_filtered, budget_filtered, feature_filtered):
        """조건 완화가 필요한 경우, 사용자에게 가이드 제공"""
        print("\n💡 매물 추천 분석:")
        
        # 위치 조건 분석
        if len(location_filtered) < 5:
            print("  • 위치 조건에 맞는 매물이 부족합니다.")
            print("    💡 추천: 반경을 확대하거나 다른 위치를 고려해보세요.")
        else:
            print("  • 위치 조건에 맞는 매물은 충분합니다.")
        
        # 예산 조건 분석
        if len(budget_filtered) < 5:
            print("  • 예산 조건에 맞는 매물이 부족합니다.")
            print("    💡 추천: 월세/보증금 예산을 약간 높이는 것을 고려해보세요.")
        else:
            print("  • 예산 조건에 맞는 매물은 충분합니다.")
        
        # 특성 조건 분석
        if len(feature_filtered) < 5:
            print("  • 매물 특성 조건에 맞는 매물이 부족합니다.")
            
            # 가장 제한적인 특성 조건 파악
            floor_filtered = any("층" in r and "층수" not in r for r in self.filtering_results)
            direction_filtered = any("향" in r for r in self.filtering_results)
            
            print("    💡 추천: 다음 조건 중 일부를 완화해보세요:")
            if floor_filtered:
                print("      - 층수 조건을 완화")
            if direction_filtered:
                print("      - 방향(남향 등) 조건을 완화")
        else:
            print("  • 매물 특성 조건에 맞는 매물은 충분합니다.")
        
        # 종합 분석
        if len(location_filtered) >= 5 and len(budget_filtered) >= 5 and len(feature_filtered) >= 5:
            print("  • 모든 조건은 개별적으로 충족하는 매물이 충분하지만, 모든 조건을 동시에 만족하는 매물이 부족합니다.")
            print("    💡 추천: 가장 중요한 조건은 유지하고 덜 중요한 조건을 완화해보세요.")
    
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
                "floor": "5층",
                "heating_type": "개별난방",
                "parking": True,
                "facilities": "에어컨, 냉장고, 세탁기",
                "view": "남향, 채광 좋음",
                "size": 8,
                "엘리베이터": "있음",
                "type": "원룸",
                "안전시설": "현관보안",
                "infra_score": 2.5,
                "feature_score": 2,  # 엘리베이터 있음(+1), 주차 가능(+1)
                "total_score": 4.5,  # infra_score + feature_score
                "infra_details": {
                    "traffic_subway": {"distance": 350, "score": 5, "nearest": "강남역"},
                    "life_park": {"distance": 450, "score": 2.5, "nearest": "역삼공원"},
                    "life_healthjang": {"distance": 200, "score": 1, "nearest": "역삼헬스센터"}
                }
            },
            {
                "address": "서울 마포구 합정동 456-78",
                "station": "합정역",
                "rent": 40,
                "deposit": 300,
                "maint": 8,
                "time_info": "도보 7분",
                "floor": "3층",
                "heating_type": "중앙난방",
                "parking": False,
                "facilities": "냉장고, 인덕션",
                "view": "서향, 한강 조망",
                "size": 6,
                "엘리베이터": "있음",
                "type": "원룸",
                "안전시설": "CCTV",
                "infra_score": 3.0,
                "feature_score": 1,  # 엘리베이터 있음(+1), 주차 불가능(+0)
                "total_score": 4.0,  # infra_score + feature_score
                "infra_details": {
                    "traffic_subway": {"distance": 400, "score": 4.5, "nearest": "합정역"},
                    "life_park": {"distance": 350, "score": 3, "nearest": "망원한강공원"},
                    "life_healthjang": {"distance": 500, "score": 0.3, "nearest": "마포헬스클럽"}
                }
            }
        ]
        
        return {
            "location_based": default_properties,
            "budget_based": default_properties,
            "feature_based": default_properties,
            "combined": default_properties,
            "filtering_results": []
        }