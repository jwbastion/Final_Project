import psycopg2
from psycopg2.extras import RealDictCursor
from liveport.utils.common_utils import haversine, format_time_info
from liveport.config import Config

# 새로 추가된 함수: 예산 초과 여부 확인
def is_budget_exceeded(prop, user_state):
    """매물이 사용자 예산을 초과하는지 확인"""
    # 사용자 예산 정보 - 객체 또는 딕셔너리 대응
    if isinstance(user_state, dict):
        rent_limit = user_state.get("rent", 100)
        deposit_limit = user_state.get("deposit", 5000)
        maint_limit = user_state.get("maint", 50)
    else:
        # 객체인 경우 속성으로 접근
        rent_limit = getattr(user_state, "monthly_rent", 100)
        deposit_limit = getattr(user_state, "budget", 5000)
        maint_limit = getattr(user_state, "maintenance_fee", 50)
    
    # 매물 가격 정보
    rent = prop.get("rent", 0) if isinstance(prop, dict) else prop.metadata.get("rent", 0)
    deposit = prop.get("deposit", 0) if isinstance(prop, dict) else prop.metadata.get("deposit", 0)
    maint = prop.get("maint", 0) if isinstance(prop, dict) else prop.metadata.get("maint", 0)
    
    # 디버깅 로그 추가
    print(f"예산 초과 확인: 월세({rent} vs {rent_limit}), 보증금({deposit} vs {deposit_limit}), 관리비({maint} vs {maint_limit})")
    
    # 초과 여부 및 초과 금액 계산
    rent_exceeded = rent > rent_limit
    deposit_exceeded = deposit > deposit_limit
    maint_exceeded = maint > maint_limit
    
    return {
        "exceeded": rent_exceeded or deposit_exceeded or maint_exceeded,
        "rent_exceeded": rent_exceeded,
        "deposit_exceeded": deposit_exceeded,
        "maint_exceeded": maint_exceeded,
        "rent_excess": max(0, rent - rent_limit),
        "deposit_excess": max(0, deposit - deposit_limit),
        "maint_excess": max(0, maint - maint_limit)
    }

# 새로 추가된 함수: 예산 내/초과 매물 분리 정렬
def sort_properties_with_budget_priority(properties, user_state):
    """예산 내 매물 우선, 그 다음 예산 초과 매물로 정렬"""
    # 예산 내 매물과 예산 초과 매물 분리
    within_budget = []
    exceeds_budget = []
    
    for prop in properties:
        budget_status = is_budget_exceeded(prop, user_state)
        
        # 예산 초과 정보 저장
        prop["budget_exceeded"] = budget_status["exceeded"]
        prop["rent_exceeded"] = budget_status["rent_exceeded"]
        prop["deposit_exceeded"] = budget_status["deposit_exceeded"]
        prop["maint_exceeded"] = budget_status["maint_exceeded"]
        prop["rent_excess"] = budget_status["rent_excess"]
        prop["deposit_excess"] = budget_status["deposit_excess"]
        prop["maint_excess"] = budget_status["maint_excess"]
        
        if budget_status["exceeded"]:
            exceeds_budget.append(prop)
        else:
            within_budget.append(prop)
    
    # 각 그룹 내에서 총점으로 정렬
    within_budget.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    exceeds_budget.sort(key=lambda x: x.get("total_score", 0), reverse=True)
    
    # 예산 내 매물 먼저, 그 다음 예산 초과 매물
    return within_budget + exceeds_budget

def remove_duplicates(properties):
    """매물 목록에서 중복 제거 (id 기준)"""
    seen_ids = set()
    unique_props = []
    
    for prop in properties:
        prop_id = prop.get("id")
        if prop_id and prop_id not in seen_ids:
            seen_ids.add(prop_id)
            unique_props.append(prop)
        elif not prop_id:  # id가 없는 경우 주소로 중복 체크
            prop_addr = prop.get("address", "")
            if prop_addr and prop_addr not in seen_ids:
                seen_ids.add(prop_addr)
                unique_props.append(prop)
    
    return unique_props

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
    
    # user_state가 딕셔너리인지 객체인지에 따라 다르게 접근
    if isinstance(user_state, dict):
        lat0 = user_state.get("lat")
        lng0 = user_state.get("lng")
        service = user_state.get("service")
    else:
        # UserState 객체인 경우 속성으로 접근
        lat0 = getattr(user_state, "lat", None)
        lng0 = getattr(user_state, "lng", None)
        service = getattr(user_state, "service", None)
    
    # 디버깅 로그 추가
    print(f"위치 필터링 시작: 서비스 유형 = {service}, 좌표 = ({lat0}, {lng0})")
    print(f"user_state 타입: {type(user_state).__name__}")
    
    if hasattr(user_state, "__dict__"):
        print(f"user_state 속성들: {user_state.__dict__}")
    
    # 사용자 좌표 검증
    if lat0 is None or lng0 is None:
        print("위치 필터링 오류: 사용자 좌표가 없습니다. 위치 필터링을 건너뜁니다.")
        return properties  # 좌표가 없으면 필터링 안 함
    
    if service == "반경":
        # 여기가 문제의 원인!
        # 수정: 객체 속성으로 접근하도록 변경
        if isinstance(user_state, dict):
            radius = user_state.get("radius", 1000)
        else:
            radius = getattr(user_state, "search_radius", 1000)
            
        print(f"반경 기준 필터링: {radius}m")
        
        for idx, prop in enumerate(properties):
            md = getattr(prop, 'metadata', prop)
            
            # 매물 좌표 검증
            plat = md.get("lat")
            plng = md.get("lng")
            if plat is None or plng is None:
                print(f"매물 #{idx+1}({md.get('address', '주소 없음')}): 좌표 없음, 건너뜀")
                continue
                
            try:
                # 명시적으로 float로 변환
                plat = float(plat)
                plng = float(plng)
                
                # 거리 계산 및 상세 로깅
                dist = haversine(lat0, lng0, plat, plng)
                address = md.get("address", "주소 없음")
                station = md.get("station", "역 없음")
                
                if dist <= radius:
                    filtered.append(prop)
                    print(f"매물 #{idx+1}({address}, {station}): 거리 {dist:.1f}m ≤ {radius}m 반경 내 포함")
                else:
                    print(f"매물 #{idx+1}({address}, {station}): 거리 {dist:.1f}m > {radius}m 반경 초과")
            except (ValueError, TypeError) as e:
                print(f"매물 #{idx+1}({md.get('address', '주소 없음')}): 좌표 변환 오류 - {e}")
                continue
    
    elif service == "소요시간":
        time_limit = user_state.get("time_limit", 30)
        movement = user_state.get("movement", "대중교통")
        key = "walk_time" if movement == "도보" else "transit_time"
        print(f"소요시간 기준 필터링: {movement}, 최대 {time_limit}분")
        
        # 가장 가까운 역 3개 찾기
        station_coords = {}
        for prop in properties:
            md = getattr(prop, 'metadata', prop)
            st, lat, lng = md.get("station"), md.get("lat"), md.get("lng")
            if st and isinstance(lat, (float, int)) and isinstance(lng, (float, int)):
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
        
        for idx, prop in enumerate(properties):
            md = getattr(prop, 'metadata', prop)
            station = md.get("station")
            time_value = md.get(key, 9999)
            
            if station in nearest and time_value <= time_limit:
                filtered.append(prop)
                print(f"매물 #{idx+1}({md.get('address', '주소 없음')}, {station}): {movement} {time_value}분 ≤ {time_limit}분 기준 내 포함")
            else:
                # 필터링 이유 로깅
                if station not in nearest:
                    print(f"매물 #{idx+1}({md.get('address', '주소 없음')}, {station}): 가까운 역 3개에 포함되지 않음")
                else:
                    print(f"매물 #{idx+1}({md.get('address', '주소 없음')}, {station}): {movement} {time_value}분 > {time_limit}분 기준 초과")
    else:
        # 상관없음
        print("위치 필터링 없음 (상관없음)")
        filtered = properties
    
    print(f"위치 필터링 결과: {len(filtered)}개 매물 (전체 {len(properties)}개 중)")
    return filtered

def filter_properties_by_budget(properties, user_state):
    """사용자가 설정한 예산 조건을 충족하는 매물 필터링"""
    # 예산 정보 접근 방식 개선
    if isinstance(user_state, dict):
        rent_limit = user_state.get("rent", 100)
        deposit_limit = user_state.get("deposit", 5000)
        maint_limit = user_state.get("maint", 50)
    else:
        # 객체인 경우 속성으로 접근
        rent_limit = getattr(user_state, "monthly_rent", 100)
        deposit_limit = getattr(user_state, "budget", 5000)
        maint_limit = getattr(user_state, "maintenance_fee", 50)

    print(f"예산 필터링 시작: 월세 {rent_limit}만원, 보증금 {deposit_limit}만원, 관리비 {maint_limit}만원")
 
    filtered = []
    for prop in properties:
        md = prop.metadata if hasattr(prop, 'metadata') else prop
        rent = md.get("rent", float("inf"))
        deposit = md.get("deposit", float("inf"))
        maint = md.get("maint", float("inf"))

        # 모두 한도 이하인 매물만 통과
        if rent <= rent_limit and deposit <= deposit_limit and maint <= maint_limit:
            filtered.append(prop)
        else:
            print(f"예산 제외: {md.get('address','')} "
                  f"(월세:{rent}>{rent_limit}, "
                  f"보증금:{deposit}>{deposit_limit}, "
                  f"관리비:{maint}>{maint_limit})")

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

# 개선된 함수 1: 매물 특성 기반 필터링
def filter_properties_by_features(properties, user_state):
    """사용자가 선호하는 매물 특성을 충족하는 매물 필터링 (개선된 버전)"""
    feature_preferences = user_state.get("property_features", {})
    if not feature_preferences:
        print("매물 특성 필터링: 설정된 선호 조건 없음")
        return properties, []
    
    print("매물 특성 필터링 시작: ", feature_preferences)
    
    # 특성별 중요도 가중치 설정 (점수화 및 단계적 필터링에 사용)
    feature_importance = {
        "elevator": 5,  # 엘리베이터 (가장 중요)
        "parking": 5,   # 주차 (가장 중요)
        "heating": 4,   # 난방 방식 (중요)
        "floor": 3,     # 층수 (중간)
        "size": 2,      # 면적 (낮음)
        "direction": 1, # 방향 (가장 낮음)
        "type": 3       # 방 타입 (중간)
    }
    
    # 특성별 필터링 결과 추적
    feature_filtering_counts = {k: 0 for k in feature_importance.keys()}
    filtering_results = []  # 필터링 이유 추적
    
    # 1단계: 기본 필터링 (모든 조건 적용)
    filtered = []
    skipped_props = []  # 필터링에서 제외된 매물
    
    for prop in properties:
        md = prop.metadata
        
        # 필터링 통과 여부 플래그
        passes_filters = True
        filter_reason = None
        failed_features = []  # 실패한 특성 목록
        
        # 필터링 로직을 함수로 분리하여 각 특성별 필터링 적용
        # 중요: "상관없음" 조건은 필터링에서 제외
        
        # 1. 엘리베이터 필터링 
        if passes_filters:
            elevator_pref = feature_preferences.get("elevator", "").lower()
            
            if elevator_pref and "상관없음" not in elevator_pref:
                elevator_text = str(md.get("elevator", md.get("엘리베이터", ""))).lower()
                elevator_required = ("있" in elevator_pref or "중요" in elevator_pref or 
                                    "네" in elevator_pref or "필요" in elevator_pref)
                elevator_exists = "있" in elevator_text or "가능" in elevator_text
                
                if elevator_required and not elevator_exists:
                    filter_reason = f"{md.get('address')} - 엘리베이터 필수지만 없어서 제외"
                    passes_filters = False
                    failed_features.append("elevator")
                    feature_filtering_counts["elevator"] += 1
        
        # 2. 주차 필터링
        if passes_filters:
            parking_pref = feature_preferences.get("parking", "").lower()
            
            if parking_pref and "상관없음" not in parking_pref:
                parking = str(md.get("parking", md.get("주차", ""))).lower()
                parking_required = ("있" in parking_pref or "중요" in parking_pref or 
                                  "네" in parking_pref or "필요" in parking_pref)
                parking_exists = "있" in parking or "가능" in parking
                
                if parking_required and not parking_exists:
                    filter_reason = f"{md.get('address')} - 주차장 필수지만 없어서 제외"
                    passes_filters = False
                    failed_features.append("parking")
                    feature_filtering_counts["parking"] += 1
        
        # 3. 난방 방식 필터링
        if passes_filters:
            heating_pref = feature_preferences.get("heating", "").lower()
            
            if heating_pref and heating_pref != "상관없음":
                heating = str(md.get("heating_type", md.get("난방", ""))).lower()
                
                if "개별난방" in heating_pref and "개별" not in heating:
                    filter_reason = f"{md.get('address')} - 개별난방이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("heating")
                    feature_filtering_counts["heating"] += 1
                elif "중앙난방" in heating_pref and "중앙" not in heating:
                    filter_reason = f"{md.get('address')} - 중앙난방이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("heating")
                    feature_filtering_counts["heating"] += 1
                elif "지역난방" in heating_pref and "지역" not in heating:
                    filter_reason = f"{md.get('address')} - 지역난방이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("heating")
                    feature_filtering_counts["heating"] += 1
        
        # 4. 층수 필터링
        if passes_filters:
            floor_pref = feature_preferences.get("floor", "").lower()
            
            if floor_pref and floor_pref != "상관없음":
                floor_str = str(md.get("floor", "")).lower()
                
                # 반지하 제외 조건
                if "반지하 제외" in floor_pref and ("반지" in floor_str or "지하" in floor_str):
                    filter_reason = f"{md.get('address')} - 반지하 제외 조건으로 제외"
                    passes_filters = False
                    failed_features.append("floor")
                    feature_filtering_counts["floor"] += 1
                else:
                    try:
                        floor_num = int(''.join(filter(str.isdigit, floor_str)))
                        
                        if "2층 이상" in floor_pref and floor_num < 2:
                            filter_reason = f"{md.get('address')} - 2층 이상 아니라서 제외"
                            passes_filters = False
                            failed_features.append("floor")
                            feature_filtering_counts["floor"] += 1
                        elif "저층" in floor_pref and (floor_num > 3 or floor_num == 0):
                            filter_reason = f"{md.get('address')} - 저층이 아니라서 제외"
                            passes_filters = False
                            failed_features.append("floor")
                            feature_filtering_counts["floor"] += 1
                        elif "중층" in floor_pref and (floor_num < 4 or floor_num > 7):
                            filter_reason = f"{md.get('address')} - 중층이 아니라서 제외"
                            passes_filters = False
                            failed_features.append("floor")
                            feature_filtering_counts["floor"] += 1
                        elif "고층" in floor_pref and floor_num < 8:
                            filter_reason = f"{md.get('address')} - 고층이 아니라서 제외"
                            passes_filters = False
                            failed_features.append("floor")
                            feature_filtering_counts["floor"] += 1
                    except:
                        # 층수를 숫자로 변환할 수 없는 경우 스킵
                        pass
        
        # 5. 면적 필터링 
        if passes_filters:
            size_pref = feature_preferences.get("size", "").lower()
            
            if size_pref and size_pref != "상관없음":
                size = md.get("size", 0)
                
                try:
                    # 문자열로 저장된 경우 숫자로 변환
                    if isinstance(size, str) and size.strip():
                        size = float(''.join(c for c in size if c.isdigit() or c == '.'))
                    
                    # 사용자 선호도에 따른 필터링
                    if "5평 이하" in size_pref and size > 5:
                        filter_reason = f"{md.get('address')} - 5평 이하가 아니라서 제외"
                        passes_filters = False
                        failed_features.append("size")
                        feature_filtering_counts["size"] += 1
                    elif "5~10평" in size_pref and (size < 5 or size > 10):
                        filter_reason = f"{md.get('address')} - 5~10평 범위가 아니라서 제외"
                        passes_filters = False
                        failed_features.append("size")
                        feature_filtering_counts["size"] += 1
                    elif "10~15평" in size_pref and (size < 10 or size > 15):
                        filter_reason = f"{md.get('address')} - 10~15평 범위가 아니라서 제외"
                        passes_filters = False
                        failed_features.append("size")
                        feature_filtering_counts["size"] += 1
                    elif "15~20평" in size_pref and (size < 15 or size > 20):
                        filter_reason = f"{md.get('address')} - 15~20평 범위가 아니라서 제외"
                        passes_filters = False
                        failed_features.append("size")
                        feature_filtering_counts["size"] += 1
                    elif "20평 이상" in size_pref and size < 20:
                        filter_reason = f"{md.get('address')} - 20평 이상이 아니라서 제외"
                        passes_filters = False
                        failed_features.append("size")
                        feature_filtering_counts["size"] += 1
                except (ValueError, TypeError):
                    # 면적 데이터 오류 시 필터링 스킵
                    pass
        
        # 6. 향 필터링
        if passes_filters:
            direction_pref = feature_preferences.get("direction", "").lower()
            
            if direction_pref and direction_pref != "상관없음":
                direction = str(md.get("direction", md.get("조망", ""))).lower()
                
                # 각 방향 확인
                if "남향" in direction_pref and "남" not in direction:
                    filter_reason = f"{md.get('address')} - 남향이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("direction")
                    feature_filtering_counts["direction"] += 1
                elif "동향" in direction_pref and "동" not in direction:
                    filter_reason = f"{md.get('address')} - 동향이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("direction")
                    feature_filtering_counts["direction"] += 1
                elif "서향" in direction_pref and "서" not in direction:
                    filter_reason = f"{md.get('address')} - 서향이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("direction")
                    feature_filtering_counts["direction"] += 1
                elif "북향" in direction_pref and "북" not in direction:
                    filter_reason = f"{md.get('address')} - 북향이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("direction")
                    feature_filtering_counts["direction"] += 1
        
        # 7. 방 타입 필터링
        if passes_filters:
            type_pref = feature_preferences.get("type", "").lower()
            
            if type_pref and type_pref != "상관없음":
                room_type = str(md.get("type", "원룸")).lower()
                
                if "원룸" in type_pref and "원룸" not in room_type:
                    filter_reason = f"{md.get('address')} - 원룸이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("type")
                    feature_filtering_counts["type"] += 1
                elif "투룸" in type_pref and "투룸" not in room_type:
                    filter_reason = f"{md.get('address')} - 투룸이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("type")
                    feature_filtering_counts["type"] += 1
                elif "쓰리룸" in type_pref and "쓰리룸" not in room_type:
                    filter_reason = f"{md.get('address')} - 쓰리룸이 아니라서 제외"
                    passes_filters = False
                    failed_features.append("type")
                    feature_filtering_counts["type"] += 1
        
        # 모든 조건 통과 시 추가
        if passes_filters:
            filtered.append(prop)
        elif filter_reason:
            # 필터링 이유 추적
            filtering_results.append(f"⚠️ 추가 필터링: {filter_reason}")
            print(f"⚠️ 추가 필터링: {filter_reason}")
            # 추가: 실패한 특성과 함께 매물 저장
            prop.failed_features = failed_features
            skipped_props.append(prop)
    
    print(f"매물 특성 필터링 결과: {len(filtered)}개 매물 (원래: {len(properties)}개)")
    
    # 필터링 결과가 너무 적은 경우 (5개 미만) 조건 완화 적용
    if len(filtered) < 5 and skipped_props:
        print("필터링 결과가 적어 조건 완화 적용")
        
        # 중요도 순으로 정렬된 특성 목록
        importance_sorted = sorted(feature_importance.items(), key=lambda x: x[1])
        
        # 덜 중요한 특성부터 조건 완화
        relaxed_features = []
        
        for feature, importance in importance_sorted:
            # 해당 특성으로 필터링된 매물이 있는 경우에만 완화 적용
            if feature_filtering_counts[feature] > 0:
                relaxed_features.append(feature)
                print(f"조건 완화 적용: {feature} 특성 필터링 무시")
                
                # 해당 특성에 의해 걸러진 매물 복원
                for prop in skipped_props:
                    if hasattr(prop, 'failed_features') and feature in prop.failed_features:
                        # 다른 실패 요인이 없거나, 다른 실패 요인도 모두 완화된 경우
                        other_fails = [f for f in prop.failed_features if f != feature and f not in relaxed_features]
                        if not other_fails:
                            filtered.append(prop)
            
            # 조건 완화 후 충분한 매물이 확보되면 중단
            if len(filtered) >= 5:
                print(f"조건 완화 후 매물 수: {len(filtered)}개 (충분)")
                break
        
        # 조건 완화 결과 기록
        if relaxed_features:
            relaxed_msg = "🔍 조건 완화 결과: "
            for feature in relaxed_features:
                feature_name = {
                    "elevator": "엘리베이터",
                    "parking": "주차",
                    "heating": "난방",
                    "floor": "층수",
                    "size": "면적",
                    "direction": "방향",
                    "type": "방 타입"
                }.get(feature, feature)
                relaxed_msg += f"'{feature_name}', "
            relaxed_msg = relaxed_msg[:-2] + " 조건을 완화했습니다."
            filtering_results.append(relaxed_msg)
            print(relaxed_msg)
    
    # 필터링 결과가 없는 경우 사용자에게 추천 사항 제공
    if len(filtered) == 0 and filtering_results:
        # 어떤 조건이 가장 많이 필터링 원인이 되었는지 분석
        filter_counts = {
            "엘리베이터": feature_filtering_counts["elevator"],
            "주차": feature_filtering_counts["parking"],
            "난방": feature_filtering_counts["heating"],
            "층수": feature_filtering_counts["floor"],
            "면적": feature_filtering_counts["size"],
            "방향": feature_filtering_counts["direction"],
            "방 타입": feature_filtering_counts["type"]
        }
        
        # 가장 많은 필터링 원인 출력
        max_filter = max(filter_counts.items(), key=lambda x: x[1])
        if max_filter[1] > 0:
            suggest_msg = f"\n🔍 분석 결과: 가장 많은 매물이 '{max_filter[0]}' 조건으로 필터링되었습니다."
            suggest_msg += f"\n💡 추천 사항: 이 조건을 '상관없음'으로 변경하면 더 많은 매물을 볼 수 있습니다."
            filtering_results.append(suggest_msg)
            print(suggest_msg)
    
    # 매물에 각 특성별 일치 여부 정보 추가 (✓/✗)
    for prop in filtered:
        md = prop.metadata if hasattr(prop, 'metadata') else prop
        match_info = {}
        
        # 엘리베이터 일치 여부
        elevator_pref = feature_preferences.get("elevator", "").lower()
        if elevator_pref and "상관없음" not in elevator_pref:
            elevator_text = str(md.get("elevator", md.get("엘리베이터", ""))).lower()
            elevator_required = ("있" in elevator_pref or "중요" in elevator_pref or 
                               "네" in elevator_pref or "필요" in elevator_pref)
            elevator_exists = "있" in elevator_text or "가능" in elevator_text
            match_info["elevator_match"] = (
                (elevator_required and elevator_exists) or 
                (not elevator_required and not elevator_exists)
            )
        else:
            match_info["elevator_match"] = None  # 상관없음
        
        # 주차 일치 여부 
        parking_pref = feature_preferences.get("parking", "").lower()
        if parking_pref and "상관없음" not in parking_pref:
            parking_text = str(md.get("parking", md.get("주차", ""))).lower()
            parking_required = ("있" in parking_pref or "중요" in parking_pref or 
                              "네" in parking_pref or "필요" in parking_pref)
            parking_exists = "있" in parking_text or "가능" in parking_text
            match_info["parking_match"] = (
                (parking_required and parking_exists) or 
                (not parking_required and not parking_exists)
            )
        else:
            match_info["parking_match"] = None  # 상관없음
        
        # 기타 특성 일치 여부 확인 (간소화를 위해 주요 특성만 확인)
        # 필요시 다른 특성에 대해서도 동일한 패턴으로 확장 가능
        
        # 일치 정보 저장
        if hasattr(prop, 'metadata'):
            prop.feature_match_info = match_info
        else:
            prop["feature_match_info"] = match_info
    
    return filtered, filtering_results

# 개선된 함수 2: 매물 특성 점수 계산 함수
def calculate_feature_scores(properties, user_state):
    # user_state에서 property_features 가져오기 (객체 또는 딕셔너리 대응)
    feature_preferences = None
    
    # 객체로 접근 시도
    if hasattr(user_state, "property_features"):
        feature_preferences = user_state.property_features
    # 딕셔너리로 접근 시도
    elif hasattr(user_state, "get"):
        feature_preferences = user_state.get("property_features", {})
    # 직접 키로 접근 시도
    elif isinstance(user_state, dict):
        feature_preferences = user_state.get("property_features", {})
    
    print(f"특성 점수 계산 시작: feature_preferences={feature_preferences}")
    
    if not feature_preferences:
        print("특성 점수 계산: 설정된 선호 조건 없음")
        # 선호도가 없을 경우 기본 점수 부여
        for prop in properties:
            prop["feature_score"] = 3.0
            prop["feature_score_details"] = ["기본 점수(3.0점)"]
            prop["total_score"] = prop.get("infra_score", 0) + 3.0
        return properties
    
    # 특성별 가중치 설정 - 중요 특성에 더 높은 가중치 부여
    feature_weights = {
        "elevator": 1.5,     # 엘리베이터 (중요)
        "parking": 1.5,      # 주차 (중요)
        "heating": 1.2,      # 난방 방식 (중요)
        "floor": 1.0,        # 층수 (보통)
        "size": 1.0,         # 면적 (보통)
        "direction": 0.8,    # 방향 (낮음)
        "type": 1.0          # 방 타입 (보통)
    }
    
    scored_properties = []
    
    for prop in properties:
        # 기존 속성 유지
        scored_prop = prop.copy() if isinstance(prop, dict) else dict(prop)
        
        # 특성 점수 및 세부 정보 초기화
        feature_scores = {}
        feature_matches = {}
        feature_details = []
        
        # 1. 층수 점수 계산
        floor_str = scored_prop.get('floor', '정보 없음')
        floor_pref = feature_preferences.get("floor", "상관없음").lower()
        
        # 층수 카테고리 결정
        floor_category = "정보 없음"
        if any(term in str(floor_str).lower() for term in ["반지하", "반지층", "반층", "지하"]):
            floor_category = "반지하/반층"
        elif "옥탑" in str(floor_str).lower():
            floor_category = "옥탑"
        else:
            try:
                floor_num = int(''.join(filter(str.isdigit, str(floor_str))))
                if 1 <= floor_num <= 3:
                    floor_category = "저층(1-3층)"
                elif 4 <= floor_num <= 7:
                    floor_category = "중층(4-7층)"
                elif floor_num >= 8:
                    floor_category = "고층(8층 이상)"
            except:
                pass
        
        # 층수 선호도에 따른 점수 및 일치 여부
        if floor_pref == "상관없음":
            floor_score = 0.5  # 상관없음이면 중간 점수
            floor_match = None  # 일치 여부 없음
        elif "2층 이상" in floor_pref:
            try:
                floor_num = int(''.join(filter(str.isdigit, str(floor_str))))
                if floor_num >= 2:
                    floor_score = 1.0  # 완전 일치
                    floor_match = True
                else:
                    floor_score = 0.1  # 불일치
                    floor_match = False
            except:
                if "반지하" in floor_category or "1층" in floor_str:
                    floor_score = 0.1  # 불일치
                    floor_match = False
                else:
                    floor_score = 0.7  # 대체로 일치
                    floor_match = True
        elif "저층" in floor_pref and "저층" in floor_category:
            floor_score = 1.0  # 완전 일치
            floor_match = True
        elif "중층" in floor_pref and "중층" in floor_category:
            floor_score = 1.0  # 완전 일치
            floor_match = True
        elif "고층" in floor_pref and "고층" in floor_category:
            floor_score = 1.0  # 완전 일치
            floor_match = True
        elif "반지하 제외" in floor_pref and "반지하" not in floor_category:
            floor_score = 0.7  # 조건 만족
            floor_match = True
        else:
            floor_score = 0.1  # 불일치
            floor_match = False
        
        # 가중치 적용
        floor_weighted_score = floor_score * feature_weights["floor"]
        feature_scores["floor"] = floor_weighted_score
        feature_matches["floor"] = floor_match
        feature_details.append(f"층수({floor_weighted_score:.1f}점)")
        
        # 2. 면적 점수 계산
        size = scored_prop.get('size', 0)
        if isinstance(size, str) and size.strip():
            try:
                size = float(''.join(c for c in size if c.isdigit() or c == '.'))
            except:
                size = 0
        
        size_pref = feature_preferences.get("size", "상관없음").lower()
        
        # 면적 선호도에 따른 점수 및 일치 여부
        if size_pref == "상관없음":
            size_score = 0.5  # 상관없음이면 중간 점수
            size_match = None  # 일치 여부 없음
        elif "5평 이하" in size_pref:
            if size <= 5:
                size_score = 1.0  # 완전 일치
                size_match = True
            elif size <= 7:  # 약간 초과
                size_score = 0.4  # 부분 일치
                size_match = False
            else:
                size_score = 0.1  # 불일치
                size_match = False
        elif "5~10평" in size_pref:
            if 5 <= size <= 10:
                size_score = 1.0  # 완전 일치
                size_match = True
            elif 3 <= size < 5 or 10 < size <= 12:  # 약간 벗어남
                size_score = 0.4  # 부분 일치
                size_match = False
            else:
                size_score = 0.1  # 불일치
                size_match = False
        elif "10~15평" in size_pref:
            if 10 <= size <= 15:
                size_score = 1.0  # 완전 일치
                size_match = True
            elif 8 <= size < 10 or 15 < size <= 17:  # 약간 벗어남
                size_score = 0.4  # 부분 일치
                size_match = False
            else:
                size_score = 0.1  # 불일치
                size_match = False
        elif "15~20평" in size_pref:
            if 15 <= size <= 20:
                size_score = 1.0  # 완전 일치
                size_match = True
            elif 13 <= size < 15 or 20 < size <= 22:  # 약간 벗어남
                size_score = 0.4  # 부분 일치
                size_match = False
            else:
                size_score = 0.1  # 불일치
                size_match = False
        elif "20평 이상" in size_pref:
            if size >= 20:
                size_score = 1.0  # 완전 일치
                size_match = True
            elif 18 <= size < 20:  # 약간 미달
                size_score = 0.4  # 부분 일치
                size_match = False
            else:
                size_score = 0.1  # 불일치
                size_match = False
        else:
            size_score = 0.5  # 기본 중간 점수
            size_match = None
        
        # 가중치 적용
        size_weighted_score = size_score * feature_weights["size"]
        feature_scores["size"] = size_weighted_score
        feature_matches["size"] = size_match
        feature_details.append(f"면적({size_weighted_score:.1f}점)")
        
        # 3. 난방 방식 점수 계산
        heating = scored_prop.get('heating_type', scored_prop.get('난방', '정보 없음')).lower()
        heating_pref = feature_preferences.get("heating", "상관없음").lower()
        
        # 난방 방식 선호도에 따른 점수 및 일치 여부
        if heating_pref == "상관없음":
            heating_score = 0.5  # 상관없음이면 중간 점수
            heating_match = None  # 일치 여부 없음
        elif "개별난방" in heating_pref and "개별" in heating:
            heating_score = 1.0  # 완전 일치
            heating_match = True
        elif "중앙난방" in heating_pref and "중앙" in heating:
            heating_score = 1.0  # 완전 일치
            heating_match = True
        elif "지역난방" in heating_pref and "지역" in heating:
            heating_score = 1.0  # 완전 일치
            heating_match = True
        else:
            heating_score = 0.1  # 불일치
            heating_match = False
        
        # 가중치 적용
        heating_weighted_score = heating_score * feature_weights["heating"]
        feature_scores["heating"] = heating_weighted_score
        feature_matches["heating"] = heating_match
        feature_details.append(f"난방({heating_weighted_score:.1f}점)")
        
        # 4. 주차 가능 여부 점수 계산
        parking_text = scored_prop.get('parking', "")
        parking = "있" in str(parking_text).lower() or "가능" in str(parking_text).lower() or parking_text is True
        parking_pref = feature_preferences.get("parking", "상관없음").lower()
        
        # 주차 선호도에 따른 점수 및 일치 여부
        if parking_pref == "상관없음":
            parking_score = 0.5  # 상관없음이면 중간 점수
            parking_match = None  # 일치 여부 없음
        elif "네" in parking_pref or "있" in parking_pref or "중요" in parking_pref or "필요" in parking_pref:
            # 주차 필요함
            if parking:
                parking_score = 1.0  # 주차 필요 & 주차 가능
                parking_match = True
            else:
                parking_score = 0.0  # 주차 필요 & 주차 불가능
                parking_match = False
        else:
            # 주차 불필요함 (아니요)
            if parking:
                parking_score = 0.3  # 주차 불필요 & 주차 가능
                parking_match = False
            else:
                parking_score = 1.0  # 주차 불필요 & 주차 불가능
                parking_match = True
        
        # 가중치 적용
        parking_weighted_score = parking_score * feature_weights["parking"]
        feature_scores["parking"] = parking_weighted_score
        feature_matches["parking"] = parking_match
        feature_details.append(f"주차({parking_weighted_score:.1f}점)")

        # 5. 엘리베이터 여부 점수 계산
        elevator_text = scored_prop.get('엘리베이터', '정보 없음')
        elevator = "있" in str(elevator_text).lower() or "가능" in str(elevator_text).lower()
        elevator_pref = feature_preferences.get("elevator", "상관없음").lower()
        
        # 엘리베이터 선호도에 따른 점수 및 일치 여부
        if elevator_pref == "상관없음":
            elevator_score = 0.5  # 상관없음이면 중간 점수
            elevator_match = None  # 일치 여부 없음
        elif "네" in elevator_pref or "있" in elevator_pref or "중요" in elevator_pref or "필요" in elevator_pref:
            # 엘리베이터 필요함
            if elevator:
                elevator_score = 1.0  # 엘리베이터 필요 & 있음
                elevator_match = True
            else:
                elevator_score = 0.0  # 엘리베이터 필요 & 없음
                elevator_match = False
        else:
            # 엘리베이터 불필요함 (아니요)
            if elevator:
                elevator_score = 0.3  # 엘리베이터 불필요 & 있음 
                elevator_match = False
            else:
                elevator_score = 1.0  # 엘리베이터 불필요 & 없음
                elevator_match = True
        
        # 가중치 적용
        elevator_weighted_score = elevator_score * feature_weights["elevator"]
        feature_scores["elevator"] = elevator_weighted_score
        feature_matches["elevator"] = elevator_match
        feature_details.append(f"엘리베이터({elevator_weighted_score:.1f}점)")
        
        # 6. 방향 일치 여부 점수 계산
        direction = scored_prop.get('view', scored_prop.get('direction', '정보 없음')).lower()
        direction_pref = feature_preferences.get("direction", "상관없음").lower()
        
        # 방향 선호도에 따른 점수 및 일치 여부
        if direction_pref == "상관없음":
            direction_score = 0.5  # 상관없음이면 중간 점수
            direction_match = None  # 일치 여부 없음
        elif "남향" in direction_pref and "남" in direction:
            direction_score = 1.0  # 완전 일치
            direction_match = True
        elif "동향" in direction_pref and "동" in direction:
            direction_score = 1.0  # 완전 일치
            direction_match = True
        elif "서향" in direction_pref and "서" in direction:
            direction_score = 1.0  # 완전 일치
            direction_match = True
        elif "북향" in direction_pref and "북" in direction:
            direction_score = 1.0  # 완전 일치
            direction_match = True
        else:
            # 일치하지 않는 방향
            direction_score = 0.1  # 불일치
            direction_match = False
        
        # 가중치 적용
        direction_weighted_score = direction_score * feature_weights["direction"]
        feature_scores["direction"] = direction_weighted_score
        feature_matches["direction"] = direction_match
        feature_details.append(f"방향({direction_weighted_score:.1f}점)")
        
        # 7. 방 타입 일치 여부 점수 계산
        room_type = scored_prop.get('type', '원룸').lower()
        type_pref = feature_preferences.get("type", "상관없음").lower()
        
        # 방 타입 선호도에 따른 점수 및 일치 여부
        if type_pref == "상관없음":
            type_score = 0.5  # 상관없음이면 중간 점수
            type_match = None  # 일치 여부 없음
        elif "원룸" in type_pref and "원룸" in room_type:
            type_score = 1.0  # 완전 일치
            type_match = True
        elif "투룸" in type_pref and "투룸" in room_type:
            type_score = 1.0  # 완전 일치
            type_match = True
        elif "쓰리룸" in type_pref and "쓰리룸" in room_type:
            type_score = 1.0  # 완전 일치
            type_match = True
        else:
            type_score = 0.1  # 불일치
            type_match = False
        
        # 가중치 적용
        type_weighted_score = type_score * feature_weights["type"]
        feature_scores["type"] = type_weighted_score
        feature_matches["type"] = type_match
        feature_details.append(f"타입({type_weighted_score:.1f}점)")
        
        # 총 특성 점수 계산 (가중치 반영)
        total_feature_score = sum(feature_scores.values())
        
        # 최종 특성 점수 조정 (최대 7점 기준)
        # 점수 범위 조정: 최소 1점, 최대 7점
        min_score = 1.0  # 최소 점수
        max_score = 7.0  # 최대 점수
        
        # 각 특성별 최대 가능 점수 합계
        max_possible_score = sum([feature_weights[feature] for feature in feature_weights])
        
        # 비례 조정된 특성 점수
        if max_possible_score > 0:
            adjusted_feature_score = min_score + (max_score - min_score) * (total_feature_score / max_possible_score)
        else:
            adjusted_feature_score = min_score  # 기본 최소 점수
        
        # 특성 일치 여부 요약 정보 생성
        feature_matches_summary = {
            "elevator": "✓" if feature_matches.get("elevator") is True else "✗" if feature_matches.get("elevator") is False else "-",
            "parking": "✓" if feature_matches.get("parking") is True else "✗" if feature_matches.get("parking") is False else "-",
            "heating": "✓" if feature_matches.get("heating") is True else "✗" if feature_matches.get("heating") is False else "-",
            "floor": "✓" if feature_matches.get("floor") is True else "✗" if feature_matches.get("floor") is False else "-",
            "size": "✓" if feature_matches.get("size") is True else "✗" if feature_matches.get("size") is False else "-",
            "direction": "✓" if feature_matches.get("direction") is True else "✗" if feature_matches.get("direction") is False else "-",
            "type": "✓" if feature_matches.get("type") is True else "✗" if feature_matches.get("type") is False else "-"
        }
        
        # 인프라 점수 (최대 3점)
        infra_score = scored_prop.get("infra_score", 0)
        infra_adjusted = min(3.0, infra_score * 3/5)
        scored_prop["infra_score"] = infra_adjusted  # 인프라 점수 조정
        
        # 결과 저장
        scored_prop["feature_score"] = adjusted_feature_score
        scored_prop["feature_score_details"] = feature_details
        scored_prop["feature_scores"] = feature_scores
        scored_prop["feature_matches"] = feature_matches_summary
        
        # 총점 계산 (인프라 점수 + 특성 점수, 최대 10점)
        scored_prop["total_score"] = infra_adjusted + adjusted_feature_score
        
        scored_properties.append(scored_prop)
    
    print(f"특성 점수 계산 완료: {len(scored_properties)}개 매물")
    return scored_properties

# 개선된 함수 3: 인프라 점수 계산 함수
def apply_infra_scores(properties, infra_preferences, infra_data, user_state=None):
    """인프라 선호도 반영하여 매물에 점수 부여 (개선된 버전)"""
    # 디버깅: infra_preferences와 infra_data 확인
    print(f"인프라 선호도: {infra_preferences}")
    infra_types = set(item.get('type', '') for item in infra_data)
    print(f"가능한 인프라 타입: {infra_types}")
    
    # 카테고리-테이블 매핑 생성
    category_to_table = {
        "노래방": "play_karaoke",
        "카페": "life_cafe",
        "편의점": "life_convenience_store",
        "마트": "life_mart",
        "병원": "health_hospital",
        "약국": "health_pharmacy",
        "지하철역": "traffic_subway",
        "버스정류장": "traffic_bus",
        "공원": "life_park",
        "영화관": "play_cinema",
        "PC방": "play_pc_cafe",
        "헬스장": "life_healthjang",
        "백화점": "life_department_store",
        "다이소": "life_daiso",
        "주민센터": "life_community_center",
        "우체국": "life_post_office",
        "경찰서": "safety_police_station"
    }
    
    # 매핑 역방향으로도 생성 (테이블명 -> 한글 카테고리명)
    table_to_category = {v: k for k, v in category_to_table.items()}
    
    # 인프라 선호도 변환 (한글 -> 테이블명)
    table_preferences = {}
    for category, score in infra_preferences.items():
        if category in category_to_table:
            # 한글 카테고리명 -> 테이블명 매핑
            table_name = category_to_table[category]
            table_preferences[table_name] = score
        elif category in infra_types:
            # 이미 테이블명인 경우 그대로 사용
            table_preferences[category] = score
    
    # 매핑된 선호도가 없으면 원래 선호도 그대로 사용
    if not table_preferences:
        table_preferences = infra_preferences
    
    # 매핑된 선호도 기준으로 정렬
    sorted_infra = sorted(table_preferences.items(), key=lambda x: x[1], reverse=True)
    
    print(f"인프라 점수 계산 시작: {len(properties)}개 매물, {len(sorted_infra)}개 인프라 유형")
    
    # 각 매물에 점수 초기화
    scored_properties = []
    
    # 인프라 세부 정보 가져오기
    infra_details = user_state.get("infra_details", {}) if user_state else {}
    
    # 도보 시간 선호도 추출 (분당 80m 기준)
    preferred_walk_time = user_state.get("preferred_walk_time", 10) if user_state else 10  # 기본값 10분
    preferred_walk_distance = preferred_walk_time * 80  # 선호하는 도보 거리 (미터)
    
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
            "infra_details": {},
            "infra_matches": {},  # 인프라 일치 정보 추가
            "id": getattr(prop, 'id', None) if hasattr(prop, 'id') else md.get("id")  # ID 보존
        }
        
        # ID가 없는 경우 생성
        if not prop_info["id"]:
            import hashlib
            temp_id = f"{prop_info['address']}_{prop_info['station']}_{prop_info['rent']}"
            prop_info["id"] = hashlib.md5(temp_id.encode()).hexdigest()
            print(f"[DEBUG] 매물 ID 생성: {prop_info['id'][:8]}... for {prop_info['address']}")
        
        if prop_info["lat"] is None or prop_info["lng"] is None:
            scored_properties.append(prop_info)
            continue
        
        # 좌표 가져오기
        plat = float(prop_info["lat"])
        plng = float(prop_info["lng"])
        
        # 총 인프라 점수 계산 (기본값 설정)
        total_score = 0
        infra_matches = {}  # 인프라 기준 충족 여부
        
        # 각 인프라 유형별로 점수 계산
        for infra_type, weight in sorted_infra:
            # 해당 인프라 데이터 필터링
            infra_items = [item for item in infra_data if item.get("type") == infra_type]
            
            if not infra_items:
                print(f"경고: {infra_type} 유형의 인프라 데이터가 없습니다.")
                continue
            
            # 사용자 가중치에 따른 중요도 보정 (원래 가중치 사용)
            # 1-5 범위의 가중치 값을 0.5-2.0 범위로 조정
            importance_factor = 0.5 + 0.375 * (weight - 1)  # 1→0.5, 3→1.25, 5→2.0
            
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
            
            # 사용자 선호 도보 거리 반영
            distance_match = None
            if nearest_name:
                # 선호 도보 거리 내에 있는지 확인 (10분 이내 거리)
                if min_dist <= preferred_walk_distance:
                    distance_match = True  # 선호 거리 이내
                elif min_dist <= preferred_walk_distance * 2:
                    distance_match = False  # 선호 거리 초과, 하지만 2배 이내
                else:
                    distance_match = None  # 선호 거리의 2배 초과
            
            # 점수 계산 (거리 기반)
            if nearest_name:
                # 기본 점수 계산 로직
                # 1. 거리 기준 조정: 5km가 넘으면 무시
                if min_dist > 5000:
                    score = 0
                # 2. 도보 거리(800m) 이내: 가중치 * (1 - 거리/1600)
                elif min_dist <= 800:
                    score = weight * (1 - min_dist/1600)
                # 3. 800m 초과: 가중치 * 0.5 * (1 - (거리-800)/4200)
                else:
                    score = max(0, weight * 0.5 * (1 - (min_dist-800)/4200))
                
                # 4. 중요도 계수 적용
                score = score * importance_factor
                
                # 5. 선호 거리 내에 있을 경우 추가 보너스
                if distance_match is True:
                    distance_bonus = min(1.0, weight * 0.2)  # 가중치의 20%까지 보너스 (최대 1.0)
                    score += distance_bonus
                
                # 점수 반올림 (소수점 첫째 자리)
                score = round(score, 1)
                
                # 점수가 있는 경우에만 인프라 세부 정보 저장
                if score > 0:
                    # 거리를 시간으로 변환 (80m/분 기준)
                    walk_time_min = round(min_dist / 80, 1)
                    
                    # 인프라 일치 정보 추가
                    infra_matches[infra_type] = {
                        "distance_match": distance_match,
                        "walk_time_min": walk_time_min,
                        "name": nearest_name
                    }
                    
                    prop_info["infra_details"][infra_type] = {
                        "distance": min_dist,
                        "score": score,
                        "nearest": nearest_name,
                        "walk_time_min": walk_time_min,
                        "importance_factor": importance_factor
                    }
                
                # 총점에 추가
                total_score += score
                
                # 인프라 세부 정보 반영 (있는 경우)
                if infra_type in infra_details:
                    infra_type_details = infra_details[infra_type]
                    brand_match = False  # 브랜드 일치 여부
                    
                    # 1. 거리 선호도 반영
                    if "common_distance" in infra_type_details:
                        try:
                            preferred_distance = int(infra_type_details["common_distance"])
                            # 선호 거리 내에 있으면 보너스
                            if min_dist <= preferred_distance * 80:  # 약 80m = 1분 도보 거리
                                distance_bonus = min(0.5, weight * 0.15)  # 가중치의 15%까지 보너스 (최대 0.5)
                                score += distance_bonus
                                prop_info["infra_details"][infra_type]["distance_bonus"] = True
                        except:
                            pass
                    
                    # 2. 브랜드/노선 선호도 반영 (강화된 버전)
                    preferred_brand_key = None
                    if infra_type == "traffic_subway":
                        preferred_brand_key = "specific_preferred_line"
                    elif infra_type in ["life_mart", "life_department_store", "life_convenience_store", 
                                       "life_cafe", "play_cinema"]:
                        preferred_brand_key = "specific_preferred_brand"
                    
                    if preferred_brand_key and preferred_brand_key in infra_type_details:
                        preferred_brand = infra_type_details[preferred_brand_key].lower()
                        if preferred_brand and nearest_name and preferred_brand in nearest_name.lower():
                            brand_bonus = min(1.0, weight * 0.2)  # 가중치의 20%까지 보너스 (최대 1.0)
                            score += brand_bonus
                            brand_match = True
                            prop_info["infra_details"][infra_type]["brand_match"] = True
                    
                    # 인프라 일치 정보 업데이트
                    if infra_type in infra_matches:
                        infra_matches[infra_type]["brand_match"] = brand_match
        
        # 인프라 일치 여부 요약 정보 생성
        infra_match_summary = {}
        for infra_type, match_info in infra_matches.items():
            # 거리 일치 여부
            distance_symbol = "✓" if match_info.get("distance_match") is True else "△" if match_info.get("distance_match") is False else "✗"
            
            # 브랜드 일치 여부
            brand_symbol = "✓" if match_info.get("brand_match") is True else ""
            
            # 시간 표시
            time_info = f"{match_info.get('walk_time_min', '?')}분"
            
            # 요약 정보 저장
            infra_match_summary[infra_type] = {
                "name": match_info.get("name", ""),
                "summary": f"{distance_symbol}{brand_symbol} {time_info}"
            }
        
        # 총점 저장 (최소 0.5, 최대 3.0)
        prop_info["infra_score"] = min(3.0, max(0.5, total_score)) if total_score > 0 else 0
        prop_info["infra_matches"] = infra_match_summary
        
        # 시간 정보 추가
        if "time_info" not in prop_info or not prop_info["time_info"]:
            prop_info["time_info"] = format_time_info(prop_info, "상관없음")
        
        # 결과 추가
        scored_properties.append(prop_info)
    
    # 인프라 점수로 매물 정렬
    scored_properties.sort(key=lambda x: x.get("infra_score", 0), reverse=True)
    print(f"인프라 점수 계산 완료: {len(scored_properties)}개 매물 점수화")
    return scored_properties

def get_location_based_properties_with_extended_budget(properties, user_state, lat0, lng0, multiplier=1.2):  # 예산 확장 비율 조정
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
        self.data_accessor = InfraDataAccessor(Config.DB_CONFIG)
        self.recursion_depth = 0  # 재귀 호출 깊이 제한
        self.filtering_results = []  # 필터링 결과 추적
    
    def _get_db_connection(self):
        """데이터베이스 연결을 반환하는 메서드"""
        return psycopg2.connect(**Config.DB_CONFIG)
    
    def search_properties(self):
        """Pinecone에서 매물 검색 - 위치 정보 활용"""
        try:
            # 사용자 위치 정보
            lat = self.user_state.get("lat")
            lng = self.user_state.get("lng")
            
            # 위치 정보가 있는 경우 메타데이터 필터 추가
            filter_params = {}
            if lat and lng:
                # 위도, 경도 기준 약 5km 반경 내 매물 검색
                lat_range = 0.045  # 약 5km (위도 기준)
                lng_range = 0.06   # 약 5km (경도 기준)
                
                filter_params = {
                    "lat": {"$gte": lat - lat_range, "$lte": lat + lat_range},
                    "lng": {"$gte": lng - lng_range, "$lte": lng + lng_range}
                }
            
            # 쿼리 실행 (메타데이터 필터 적용)
            resp = self.index.query(
                vector=[0.0]*1536,  # 벡터 검색은 그대로 유지
                top_k=500,
                include_metadata=True,
                filter=filter_params
            )
            return resp.matches
        except Exception as e:
            print(f"Pinecone 검색 오류: {e}")
            return []
    
    def get_all_infra_data(self):
        """모든 인프라 데이터 로드"""
        infra_data = []
        
        # 인프라 선호도 확인 (여러 접근 방법 시도)
        preferences = {}
        if hasattr(self.user_state, "infra_preferences"):
            preferences = self.user_state.infra_preferences
        elif hasattr(self.user_state, "get"):
            preferences = self.user_state.get("infra_preferences", {})
        elif isinstance(self.user_state, dict):
            preferences = self.user_state.get("infra_preferences", {})
        
        print(f"인프라 선호도 확인: {preferences}")  # 디버깅용
        
        if not preferences:
            print("인프라 선호도가 설정되지 않았습니다!")
            return []
            
        for infra_type in preferences.keys():
            print(f"인프라 데이터 로드 중: {infra_type}")  # 디버깅용
            type_data = self.data_accessor.get_infra_data(infra_type)
            infra_data.extend(type_data)
        
        print(f"총 {len(infra_data)}개 인프라 데이터 로드 완료")  # 디버깅용
        return infra_data
        
    def _get_virtual_infra_data(self, infra_type):
        """인프라 데이터를 가져올 수 없을 때 가상 데이터 사용"""
        # 기본 가상 데이터
        virtual_data = {
            "life_park": [
                {"name": "창동근린공원", "lat": 37.653, "lng": 127.047, "type": "life_park"},
                {"name": "쌍문근린공원", "lat": 37.648, "lng": 127.039, "type": "life_park"},
                {"name": "초안산근린공원", "lat": 37.642, "lng": 127.025, "type": "life_park"}
            ],
            "traffic_subway": [
                {"name": "창동역", "lat": 37.653, "lng": 127.047, "type": "traffic_subway"},
                {"name": "쌍문역", "lat": 37.648, "lng": 127.035, "type": "traffic_subway"},
                {"name": "노원역", "lat": 37.655, "lng": 127.063, "type": "traffic_subway"}
            ]
        }
        
        return virtual_data.get(infra_type, [])
                  
    def get_recommendations(self, is_retry=False):
        """추천 매물 검색 및 필터링"""
        
        # 현재 설정된 위치 출력
        print(f"현재 설정된 위치: lat={self.user_state.get('lat')}, lng={self.user_state.get('lng')}")
        
        # 재귀 호출 깊이 제한
        self.recursion_depth += 1
        if self.recursion_depth > 3:
            self.recursion_depth = 0
            return {"location_based": [], "budget_based": [], "combined": []}
        
        try:
            # 초기화
            self.filtering_results = []
            
            # 모든 매물 검색
            all_properties = self.search_properties()
            
            if not all_properties:
                return self.get_default_recommendations()
            
            # 1. 위치 기반 필터링
            location_filtered = filter_properties_by_location(all_properties, self.user_state)
            
            # 2. 예산 기반 필터링
            budget_filtered = filter_properties_by_budget(all_properties, self.user_state)
            
            # 3. 매물 특성 필터링 (개선된 버전 사용)
            feature_filtered, feature_filtering_results = filter_properties_by_features(all_properties, self.user_state)
            
            # 필터링 결과 저장
            self.filtering_results.extend(feature_filtering_results)
            
            # 4. 종합 추천 (위치 + 예산 + 특성 조건 모두 충족)
            combined_filtered = self._get_combined_properties(location_filtered, budget_filtered, feature_filtered)
            
            # 5. 인프라 데이터 로드
            infra_data = self.get_all_infra_data()
            
            # 6. 인프라 점수 적용 (개선된 버전 사용)
            location_scored = apply_infra_scores(
                location_filtered, 
                self.user_state.get("infra_preferences", {}), 
                infra_data,
                self.user_state
            )
            
            # 7. 특성 점수 계산 (개선된 버전 사용)
            location_scored = calculate_feature_scores(location_scored, self.user_state)
            
            budget_scored = apply_infra_scores(
                budget_filtered, 
                self.user_state.get("infra_preferences", {}), 
                infra_data,
                self.user_state
            )
            # 특성 점수 계산 (개선된 버전 사용)
            budget_scored = calculate_feature_scores(budget_scored, self.user_state)
            
            feature_scored = apply_infra_scores(
                feature_filtered,
                self.user_state.get("infra_preferences", {}),
                infra_data,
                self.user_state
            )
            # 특성 점수 계산 (개선된 버전 사용)
            feature_scored = calculate_feature_scores(feature_scored, self.user_state)
            
            combined_scored = apply_infra_scores(
                combined_filtered,
                self.user_state.get("infra_preferences", {}),
                infra_data,
                self.user_state
            )
            # 특성 점수 계산 (개선된 버전 사용)
            combined_scored = calculate_feature_scores(combined_scored, {
    "property_features": getattr(self, "property_features", {})
})
            
            # 8. 종합 매물이 5개 미만일 경우 조건 완화 처리
            if len(combined_scored) < 5:
                combined_scored = self._enhance_recommendations(
                    combined_scored, 
                    location_scored, 
                    all_properties, 
                    infra_data
                )
            
            # 9. 각 추천 그룹에 예산 초과 여부 표시 및 정렬 
            if combined_scored:
                combined_scored = sort_properties_with_budget_priority(combined_scored, self.user_state)

            if location_scored:
                location_scored = sort_properties_with_budget_priority(location_scored, self.user_state)
                
            if budget_scored:
                budget_scored = sort_properties_with_budget_priority(budget_scored, self.user_state)

            if feature_scored:
                feature_scored = sort_properties_with_budget_priority(feature_scored, self.user_state)

            # 전체 결과에서 중복 매물 ID 추적
            all_property_ids = set()

            # 10. 중복 제거 (카테고리 간 중복도 제거)
            combined_scored = remove_duplicates(combined_scored)
            for prop in combined_scored:
                all_property_ids.add(prop.get("id"))

            # 다른 카테고리에서는 종합 추천에 포함되지 않은 매물만 유지
            location_scored = [
                prop for prop in remove_duplicates(location_scored) 
                if prop.get("id") not in all_property_ids
            ]

            budget_scored = [
                prop for prop in remove_duplicates(budget_scored) 
                if prop.get("id") not in all_property_ids
            ]

            feature_scored = [
                prop for prop in remove_duplicates(feature_scored) 
                if prop.get("id") not in all_property_ids
            ]
            
            # 재귀 깊이 초기화
            self.recursion_depth = 0
            
            return {
                "location_based": location_scored[:5],
                "budget_based": budget_scored[:5],
                "feature_based": feature_scored[:5],
                "combined": combined_scored[:5],
                "filtering_results": self.filtering_results
            }
        except Exception as e:
            print(f"추천 매물 가져오기 중 오류 발생: {e}")
            return self.get_default_recommendations()
    
    def _get_combined_properties(self, location_filtered, budget_filtered, feature_filtered):
        """종합 추천 매물 구하기"""
        location_ids = {getattr(prop, 'id', None) for prop in location_filtered}
        budget_ids = {getattr(prop, 'id', None) for prop in budget_filtered}
        feature_ids = {getattr(prop, 'id', None) for prop in feature_filtered}
        
        combined_filtered = []
        for prop in location_filtered:
            prop_id = getattr(prop, 'id', None)
            if prop_id in budget_ids and prop_id in feature_ids:
                combined_filtered.append(prop)
        
        return combined_filtered
    
    def _enhance_recommendations(self, combined_scored, location_scored, all_properties, infra_data):
        """조건 완화하여 추천 매물 개선"""
        # 기존 종합 추천 매물 수 저장 및 ID 추적
        original_count = len(combined_scored)
        existing_ids = {prop.get("id") for prop in combined_scored}
        
        # 1) 위치 기반 매물 추가
        combined_scored = self._add_properties_from_location(
            combined_scored, location_scored, existing_ids
        )
        
        # 2) 위치 + 확장 예산 매물 추가 (필요한 경우)
        if len(combined_scored) < 5:
            combined_scored = self._add_properties_with_extended_budget(
                combined_scored, all_properties, existing_ids, infra_data
            )
        
        # total_score 기준 다시 정렬
        combined_scored.sort(key=lambda x: x.get("total_score", 0), reverse=True)
        
        return combined_scored
    
    def _add_properties_from_location(self, combined_scored, location_scored, existing_ids):
        """위치 기반 매물 추가"""
        if len(combined_scored) >= 5 or not location_scored:
            return combined_scored
            
        # 위치 기반 매물 중 중복되지 않는 것만 선택
        additional_from_location = [
            prop for prop in location_scored 
            if prop.get("id") not in existing_ids
        ]
        
        # 필요한 수 계산
        need_more = 5 - len(combined_scored)
        
        # 매물 추가
        for prop in additional_from_location[:need_more]:
            combined_scored.append(prop)
            existing_ids.add(prop.get("id"))
        
        return combined_scored

    def _add_properties_with_extended_budget(self, combined_scored, all_properties, existing_ids, infra_data):
        """위치 + 확장 예산 매물 추가"""
        if len(combined_scored) >= 5:
            return combined_scored
            
        # 위치 + 확장 예산 매물 찾기
        lat0 = self.user_state.get("lat")
        lng0 = self.user_state.get("lng")
        
        # 위치 만족하면서 예산 확장한 매물 찾기 (예산 확장 비율 낮추기)
        extended_budget_props = get_location_based_properties_with_extended_budget(
            all_properties,
            self.user_state,
            lat0,
            lng0,
            multiplier=1.2  # 예산 20% 증가 (기존 50%에서 조정)
        )
        
        # 특성 필터링 적용 (개선된 버전 사용)
        extended_budget_props_filtered, _ = filter_properties_by_features(extended_budget_props, self.user_state)
        
        # 인프라 점수 계산 (개선된 버전 사용)
        extended_scored = apply_infra_scores(
            extended_budget_props_filtered,
            self.user_state.get("infra_preferences", {}),
            infra_data,
            self.user_state
        )
        
        # 특성 점수 계산 (개선된 버전 사용)
        extended_scored = calculate_feature_scores(extended_scored, self.user_state)
        
        # 필요한 수 계산
        need_more = 5 - len(combined_scored)
        
        # 이미 추가된 ID 제외하고 추가
        for prop in extended_scored:
            if prop.get("id") not in existing_ids and len(combined_scored) < 5:
                # 예산 초과 정보 추가
                budget_status = is_budget_exceeded(prop, self.user_state)
                prop["budget_exceeded"] = budget_status["exceeded"]
                prop["rent_exceeded"] = budget_status["rent_exceeded"]
                prop["deposit_exceeded"] = budget_status["deposit_exceeded"]
                prop["maint_exceeded"] = budget_status["maint_exceeded"]
                prop["rent_excess"] = budget_status["rent_excess"]
                prop["deposit_excess"] = budget_status["deposit_excess"]
                prop["maint_excess"] = budget_status["maint_excess"]
                
                combined_scored.append(prop)
                existing_ids.add(prop.get("id"))
        
        return combined_scored

    def _format_properties_to_recommendations(self, db_properties):
        """데이터베이스 매물을 추천 형식으로 변환"""
        formatted_properties = []
        
        for prop in db_properties:
            # 기본 정보 설정
            formatted_prop = {
                "address": prop.get("address", "주소 정보 없음"),
                "station": prop.get("station", "역 정보 없음"),
                "rent": prop.get("monthly_rent", 0),
                "deposit": prop.get("deposit", 0),
                "maint": prop.get("maintenance_fee", 0),
                "lat": prop.get("latitude"),
                "lng": prop.get("longitude"),
                "floor": prop.get("floor", "정보 없음"),
                "heating_type": prop.get("heating_type", "정보 없음"),
                "parking": prop.get("parking", False),
                "elevator": prop.get("elevator", False),
                "type": prop.get("property_type", "원룸"),
                "size": prop.get("size", 0),
                "direction": prop.get("direction", "정보 없음"),
                "facilities": prop.get("facilities", "정보 없음"),
                
                # 점수 정보 (실제 데이터가 없으면 기본값 설정)
                "infra_score": 2.5,
                "feature_score": 4.5,
                "total_score": 7.0,
                
                # 인프라 정보 (실제 데이터가 없으면 근처 인프라 정보로 설정)
                "infra_details": {
                    "편의점": {"nearest": "근처 편의점", "distance": 200, "score": 1.0},
                    "지하철역": {"nearest": prop.get("station", "가까운 역"), "distance": 500, "score": 1.0},
                    "대형마트": {"nearest": "근처 마트", "distance": 800, "score": 0.5}
                }
            }
            
            # 시간 정보 설정
            formatted_prop["time_info"] = f"도보 {prop.get('walk_time', 5)}분"
            
            formatted_properties.append(formatted_prop)
        
        return formatted_properties
    
    def get_default_recommendations(self):
        """조건에 맞는 매물이 없을 때 기본 추천 매물"""
        try:
            # 기본 조건으로 데이터베이스에서 매물 가져오기
            conn = self._get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 기본 조건: 적절한 가격대, 평점 높은 매물
            cursor.execute("""
                SELECT * FROM officetels
                WHERE monthly_rent <= %s AND deposit <= %s
                ORDER BY rating DESC, (monthly_rent + deposit/100) ASC
                LIMIT 5
            """, (60, 1000))  # 기본값: 월세 60만원, 보증금 1000만원 이하
            
            properties = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if properties and len(properties) > 0:
                # 데이터베이스에서 가져온 실제 매물 사용
                scored_properties = self._format_properties_to_recommendations(properties)
                return {
                    "location_based": scored_properties,
                    "budget_based": scored_properties,
                    "combined": scored_properties,
                    "filtering_results": []
                }
        except Exception as e:
            print(f"기본 추천 매물 조회 오류: {e}")
        
        # 기본 매물 정보 (특성 일치 정보 추가)
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
                "feature_score": 2.5,
                "total_score": 5.0,
                "feature_matches": {
                    "elevator": "✓",
                    "parking": "✓",
                    "heating": "✓",
                    "floor": "-",
                    "size": "-",
                    "direction": "✓",
                    "type": "-"
                },
                "infra_details": {
                    "traffic_subway": {"distance": 350, "score": 5, "nearest": "강남역"},
                    "life_park": {"distance": 450, "score": 2.5, "nearest": "역삼공원"},
                    "life_healthjang": {"distance": 200, "score": 1, "nearest": "역삼헬스센터"}
                },
                "infra_matches": {
                    "traffic_subway": {"name": "강남역", "summary": "✓ 4.4분"},
                    "life_park": {"name": "역삼공원", "summary": "✓ 5.6분"},
                    "life_healthjang": {"name": "역삼헬스센터", "summary": "✓ 2.5분"}
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
                "feature_score": 1.5,
                "total_score": 4.5,
                "feature_matches": {
                    "elevator": "✓",
                    "parking": "✗",
                    "heating": "✗",
                    "floor": "✓",
                    "size": "-",
                    "direction": "✓",
                    "type": "-"
                },
                "infra_details": {
                    "traffic_subway": {"distance": 400, "score": 4.5, "nearest": "합정역"},
                    "life_park": {"distance": 350, "score": 3, "nearest": "망원한강공원"},
                    "life_healthjang": {"distance": 500, "score": 0.3, "nearest": "마포헬스클럽"}
                },
                "infra_matches": {
                    "traffic_subway": {"name": "합정역", "summary": "✓ 5.0분"},
                    "life_park": {"name": "망원한강공원", "summary": "✓ 4.4분"},
                    "life_healthjang": {"name": "마포헬스클럽", "summary": "△ 6.3분"}
                }
            }
        ]

        # 기본 매물에도 예산 초과 여부 표시
        for prop in default_properties:
            budget_status = is_budget_exceeded(prop, self.user_state)
            prop["budget_exceeded"] = budget_status["exceeded"]
            prop["rent_exceeded"] = budget_status["rent_exceeded"]
            prop["deposit_exceeded"] = budget_status["deposit_exceeded"]
            prop["maint_exceeded"] = budget_status["maint_exceeded"]
            prop["rent_excess"] = budget_status["rent_excess"]
            prop["deposit_excess"] = budget_status["deposit_excess"]
            prop["maint_excess"] = budget_status["maint_excess"]
        
        return {
            "location_based": default_properties,
            "budget_based": default_properties,
            "feature_based": default_properties,
            "combined": default_properties,
            "filtering_results": []
        }