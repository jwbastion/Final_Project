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
        
        # 새로운 테이블 구조에 맞는 쿼리 매핑
        query_map = {
            # 교통 시설
            "traffic_subway": """
                SELECT business_name AS name, longitude, latitude 
                FROM traffic_subway
            """,
            "traffic_bus": """
                SELECT business_name AS name, longitude, latitude 
                FROM traffic_bus
            """,
            
            # 생활 편의시설
            "life_mart": """
                SELECT business_name AS name, longitude, latitude 
                FROM life_mart
            """,
            "life_department": """
                SELECT business_name AS name, longitude, latitude 
                FROM life_department
            """,
            "life_park": """
                SELECT business_name AS name, longitude, latitude 
                FROM life_park
            """,
            "life_cafe": """
                SELECT business_name AS name, longitude, latitude 
                FROM life_cafe
            """,
            
            # 의료 시설
            "health_hospital": """
                SELECT business_name AS name, longitude, latitude 
                FROM health_hospital
            """,
            "health_pharmacy": """
                SELECT business_name AS name, longitude, latitude 
                FROM health_pharmacy
            """,
            "health_gym": """
                SELECT business_name AS name, longitude, latitude 
                FROM health_gym
            """,
            
            # 오락 시설
            "play_cinema": """
                SELECT business_name AS name, longitude, latitude 
                FROM play_cinema
            """,
            "play_golf": """
                SELECT business_name AS name, longitude, latitude 
                FROM play_golf
            """,
            "play_pc_cafe": """
                SELECT business_name AS name, longitude, latitude 
                FROM play_pc_cafe
            """,
            "play_karaoke": """
                SELECT business_name AS name, longitude, latitude 
                FROM play_karaoke
            """,
            "play_facility": """
                SELECT business_name AS name, longitude, latitude 
                FROM play_facility
            """,
            
            # 안전 시설
            "safety_police_station": """
                SELECT business_name AS name, longitude, latitude 
                FROM safety_police_station
            """,
            
            # 행정 시설
            "admin_post_office": """
                SELECT business_name AS name, longitude, latitude 
                FROM admin_post_office
            """
        }
        
        # 이전 코드와의 호환성을 위한 매핑
        legacy_mapping = {
            "subway": "traffic_subway",
            "bus": "traffic_bus",
            "bigmart": "life_mart",
            "department_store": "life_department",
            "park": "life_park",
            "health": "health_hospital",
            "cinema": "play_cinema",
            "golf": "play_golf",
            "pc": "play_pc_cafe",
            "play": "play_facility",
            "police": "safety_police_station",
            "post_office": "admin_post_office",
            "sing": "play_karaoke"
        }
        
        # 이전 코드 호환성 처리
        if infra_type in legacy_mapping:
            infra_type = legacy_mapping[infra_type]
        
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
                        continue
            
            print(f"{infra_type} 표준화된 데이터 {len(standardized_results)}개 준비 완료")
            return standardized_results
            
        except Exception as e:
            print(f"쿼리 실행 오류: {e}")
            return []
