from utils.distance import haversine
from utils.formatter import format_time_info

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
    """인프라 선호도 반영하여 매물에 점수 부여"""
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
            "floor": md.get("floor", "층수 정보 없음"),
            "heating_type": md.get("heating_type", "난방 정보 없음"),
            "parking": md.get("parking", False),
            "facilities": md.get("facilities", "시설 정보 없음"),
            "view": md.get("view", "조망 정보 없음"),
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

class RealEstateRecommender:
    def __init__(self, vector_service, user_state, data_accessor):
        self.vector_service = vector_service
        self.user_state = user_state
        self.data_accessor = data_accessor
        self.recursion_depth = 0  # 재귀 호출 깊이 제한
    
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
        all_properties = self.vector_service.search_properties()
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
                "floor": "5층",
                "heating_type": "개별난방",
                "parking": True,
                "facilities": "에어컨, 냉장고, 세탁기",
                "view": "남향, 채광 좋음",
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
                "floor": "3층",
                "heating_type": "중앙난방",
                "parking": False,
                "facilities": "냉장고, 인덕션",
                "view": "서향, 한강 조망",
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