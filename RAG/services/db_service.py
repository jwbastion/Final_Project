import psycopg2
from psycopg2.extras import RealDictCursor

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
        
        # 실제 테이블 구조에 맞춘 쿼리 매핑
        query_map = {
            # 교통
            "traffic_subway": "SELECT business_name AS name, longitude, latitude FROM traffic_subway",
            "traffic_bus":     "SELECT business_name AS name, longitude, latitude FROM traffic_bus",

            # 생활편의
            "life_mart":               "SELECT business_name AS name, longitude, latitude FROM life_mart",
            "life_cafe":               "SELECT business_name AS name, longitude, latitude FROM life_cafe",
            "life_park":               "SELECT business_name AS name, longitude, latitude FROM life_park",
            "life_community_center":   "SELECT business_name AS name, longitude, latitude FROM life_community_center",
            "life_convenience_store":  "SELECT business_name AS name, longitude, latitude FROM life_convenience_store",
            "life_daiso":              "SELECT business_name AS name, longitude, latitude FROM life_daiso",
            "life_department_store":   "SELECT business_name AS name, longitude, latitude FROM life_department_store",
            "life_post_office":        "SELECT business_name AS name, longitude, latitude FROM life_post_office",

            # 의료
            "health_hospital": "SELECT business_name AS name, longitude, latitude FROM health_hospital",
            "health_pharmacy": "SELECT business_name AS name, longitude, latitude FROM health_pharmacy",

            # 오락
            "play_cinema":    "SELECT business_name AS name, longitude, latitude FROM play_cinema",
            "play_pc_cafe":   "SELECT business_name AS name, longitude, latitude FROM play_pc_cafe",
            "play_karaoke":   "SELECT business_name AS name, longitude, latitude FROM play_karaoke",

            # 안전
            "safety_police_station": "SELECT business_name AS name, longitude, latitude FROM safety_police_station",

            # 기타
            "officetels": "SELECT building_name AS name, longitude, latitude FROM officetels"
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