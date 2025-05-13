import psycopg2
from psycopg2.extras import RealDictCursor
from config import DB_CONFIG

def check_db_tables():
    """DB 테이블 존재 여부 확인"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 테이블 목록 조회
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print("=== 데이터베이스 테이블 목록 ===")
        for table in tables:
            print(f"- {table[0]}")
        
        cursor.close()
        conn.close()
        
        return tables
    except Exception as e:
        print(f"DB 테이블 조회 오류: {e}")
        return []

def check_recommendations(user_uuid):
    """특정 사용자의 추천 결과 조회"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        tables = ["combined_recommendations", "budget_recommendations", "location_recommendations"]
        
        print(f"\n=== 사용자 {user_uuid}의 추천 결과 확인 ===")
        
        for table in tables:
            # 테이블 존재 여부 확인
            cursor.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = '{table}'
                );
            """)
            
            if cursor.fetchone()['exists']:
                # 테이블 존재하면 데이터 조회
                cursor.execute(f"""
                    SELECT COUNT(*) as count
                    FROM {table}
                    WHERE user_uuid = %s
                """, (user_uuid,))
                
                count = cursor.fetchone()['count']
                print(f"{table}: {count}개 결과")
                
                if count > 0:
                    cursor.execute(f"""
                        SELECT * FROM {table}
                        WHERE user_uuid = %s
                        LIMIT 3
                    """, (user_uuid,))
                    
                    results = cursor.fetchall()
                    print(f"  샘플 데이터:")
                    for i, result in enumerate(results, 1):
                        print(f"  {i}. 주소: {result.get('address')} - 월세: {result.get('rent')}만원, 보증금: {result.get('deposit')}만원")
            else:
                print(f"{table}: 테이블이 존재하지 않음")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"추천 결과 조회 오류: {e}")

def create_recommendation_tables():
    """추천 결과 저장용 테이블 생성"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 테이블 생성 쿼리
        tables = {
            "combined_recommendations": """
                CREATE TABLE IF NOT EXISTS combined_recommendations (
                    id SERIAL PRIMARY KEY,
                    user_uuid VARCHAR(255) NOT NULL,
                    property_id VARCHAR(255) NOT NULL,
                    address TEXT,
                    station VARCHAR(255),
                    rent DOUBLE PRECISION,
                    deposit DOUBLE PRECISION,
                    maint DOUBLE PRECISION,
                    floor VARCHAR(50),
                    heating_type VARCHAR(50),
                    parking BOOLEAN,
                    facilities TEXT,
                    view TEXT,
                    lat DOUBLE PRECISION,
                    lng DOUBLE PRECISION,
                    infra_score DOUBLE PRECISION,
                    time_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "budget_recommendations": """
                CREATE TABLE IF NOT EXISTS budget_recommendations (
                    id SERIAL PRIMARY KEY,
                    user_uuid VARCHAR(255) NOT NULL,
                    property_id VARCHAR(255) NOT NULL,
                    address TEXT,
                    station VARCHAR(255),
                    rent DOUBLE PRECISION,
                    deposit DOUBLE PRECISION,
                    maint DOUBLE PRECISION,
                    lat DOUBLE PRECISION,
                    lng DOUBLE PRECISION,
                    infra_score DOUBLE PRECISION,
                    time_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "location_recommendations": """
                CREATE TABLE IF NOT EXISTS location_recommendations (
                    id SERIAL PRIMARY KEY,
                    user_uuid VARCHAR(255) NOT NULL,
                    property_id VARCHAR(255) NOT NULL,
                    address TEXT,
                    station VARCHAR(255),
                    rent DOUBLE PRECISION,
                    deposit DOUBLE PRECISION,
                    maint DOUBLE PRECISION,
                    lat DOUBLE PRECISION,
                    lng DOUBLE PRECISION,
                    infra_score DOUBLE PRECISION,
                    time_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
        
        # 테이블 생성
        for table_name, query in tables.items():
            print(f"테이블 {table_name} 생성 중...")
            cursor.execute(query)
        
        conn.commit()
        print("추천 테이블이 성공적으로 생성되었습니다.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"테이블 생성 오류: {e}")

if __name__ == "__main__":
    # 존재하는 테이블 확인
    tables = check_db_tables()
    
    # 테이블이 없으면 생성
    if not any('recommendations' in table[0] for table in tables):
        create_recommendation_tables()
        print("테이블이 생성되었습니다. 다시 확인합니다.")
        check_db_tables()
    
    # 특정 사용자의 추천 결과 확인
    user_uuid = input("확인할 사용자 UUID를 입력하세요: ")
    if user_uuid:
        check_recommendations(user_uuid)