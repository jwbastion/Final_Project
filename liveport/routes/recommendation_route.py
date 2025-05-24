from flask import Blueprint, request, jsonify, g
from liveport.services.auth_service import token_required
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app

recommendation_bp = Blueprint('recommendation', __name__, url_prefix='/api/recommendations')

def get_db_connection():
    """데이터베이스 연결"""
    conn = psycopg2.connect(**current_app.config['DB_CONFIG'])
    conn.set_client_encoding('UTF8')
    return conn

@recommendation_bp.route('/location', methods=['GET'])
@token_required
def get_location_based_recommendations():
    """거리 기반 추천 매물"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM location_recommendations 
            WHERE user_uuid = %s 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (g.user_uuid,))
        
        properties = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'properties': properties,
            'count': len(properties),
            'message': '거리 기반 추천 매물을 성공적으로 가져왔습니다.'
        })
        
    except Exception as e:
        print(f"거리 기반 추천 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'거리 기반 추천 중 오류가 발생했습니다: {str(e)}'
        }), 500

@recommendation_bp.route('/budget', methods=['GET'])
@token_required
def get_budget_based_recommendations():
    """예산 기반 추천 매물"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM budget_recommendations 
            WHERE user_uuid = %s 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (g.user_uuid,))
        
        properties = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'properties': properties,
            'count': len(properties),
            'message': '예산 기반 추천 매물을 성공적으로 가져왔습니다.'
        })
        
    except Exception as e:
        print(f"예산 기반 추천 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'예산 기반 추천 중 오류가 발생했습니다: {str(e)}'
        }), 500

@recommendation_bp.route('/combined', methods=['GET'])
@token_required
def get_combined_recommendations():
    """종합 추천 매물"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM combined_recommendations 
            WHERE user_uuid = %s 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (g.user_uuid,))
        
        properties = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'properties': properties,
            'count': len(properties),
            'message': '종합 추천 매물을 성공적으로 가져왔습니다.'
        })
        
    except Exception as e:
        print(f"종합 추천 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'종합 추천 중 오류가 발생했습니다: {str(e)}'
        }), 500

@recommendation_bp.route('/property/<string:property_id>', methods=['GET'])
@token_required
def get_property_detail(property_id):
    """매물 상세 정보 조회"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 여러 추천 테이블에서 매물 검색
        property_data = None
        for table in ['budget_recommendations', 'location_recommendations', 'combined_recommendations']:
            cursor.execute(f"""
                SELECT * FROM {table} 
                WHERE property_id = %s AND user_uuid = %s 
                LIMIT 1
            """, (property_id, g.user_uuid))
            
            result = cursor.fetchone()
            if result:
                property_data = dict(result)
                break
        
        if not property_data:
            return jsonify({
                'success': False,
                'message': '매물 정보를 찾을 수 없습니다.'
            }), 404
        
        # 주변 인프라 정보 추가 (거리 계산)
        property_lat = property_data.get('lat')
        property_lng = property_data.get('lng')
        
        nearby_infra = []
        seen_locations = set()  # 중복 위치 추적
        
        nearby_infra = []
        if property_lat and property_lng:
            # 주요 인프라 테이블들에서 가까운 시설 찾기
            infra_tables = [
                ('traffic_subway', '지하철역'),
                ('traffic_bus', '버스정류장'),
                ('life_mart', '마트'),
                ('life_convenience_store', '편의점'),
                ('life_cafe', '카페'),
                ('health_hospital', '병원'),
                ('health_pharmacy', '약국')
            ]
            
            for table_name, korean_name in infra_tables:
                try:
                    cursor.execute(f"""
                        SELECT business_name as name, latitude as lat, longitude as lng,
                               (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) 
                               * cos(radians(longitude) - radians(%s)) + sin(radians(%s)) 
                               * sin(radians(latitude)))) * 1000 AS distance
                        FROM {table_name}
                        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
                        ORDER BY distance
                        LIMIT 1  -- 각 타입별로 1개씩만
                    """, (property_lat, property_lng, property_lat))
                    
                    result = cursor.fetchone()
                    if result and result['distance'] <= 1000:
                        # 중복 체크 (동일한 이름과 위치)
                        location_key = f"{result['name']}-{result['lat']}-{result['lng']}"
                        if location_key not in seen_locations:
                            nearby_infra.append({
                                'type': korean_name,
                                'name': result['name'],
                                'distance': round(result['distance'])
                            })
                            seen_locations.add(location_key)
                            
                except Exception as e:
                    print(f"{table_name} 테이블 조회 오류: {e}")
                    continue
        
        # 거리순으로 정렬
        nearby_infra.sort(key=lambda x: x['distance'])
        
        cursor.close()
        conn.close()
        
        property_data['nearby_infra'] = nearby_infra
        
        return jsonify({
            'success': True,
            'property': property_data,
            'message': '매물 상세 정보를 성공적으로 가져왔습니다.'
        })
        
    except Exception as e:
        print(f"매물 상세 조회 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'매물 상세 정보 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500

@recommendation_bp.route('/chatbot', methods=['GET'])
@token_required
def get_chatbot_recommendations():
    """챗봇 기반 추천 매물 (종합 추천과 동일)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT * FROM combined_recommendations 
            WHERE user_uuid = %s 
            ORDER BY created_at DESC 
            LIMIT 20
        """, (g.user_uuid,))
        
        properties = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'has_recommendations': len(properties) > 0,
            'properties': properties,
            'count': len(properties),
            'message': '챗봇 기반 추천 매물을 성공적으로 가져왔습니다.' if properties else '챗봇과의 대화를 완료한 후 추천 매물을 확인할 수 있습니다.'
        })
        
    except Exception as e:
        print(f"챗봇 기반 추천 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'챗봇 기반 추천 중 오류가 발생했습니다: {str(e)}'
        }), 500

@recommendation_bp.route('/all', methods=['GET'])
@token_required
def get_all_recommendations():
    """모든 추천 매물 (메인 페이지용)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 거리 기반 추천
        cursor.execute("""
            SELECT * FROM location_recommendations 
            WHERE user_uuid = %s 
            ORDER BY created_at DESC 
            LIMIT 20
        """, (g.user_uuid,))
        location_based = cursor.fetchall()
        
        # 예산 기반 추천
        cursor.execute("""
            SELECT * FROM budget_recommendations 
            WHERE user_uuid = %s 
            ORDER BY created_at DESC 
            LIMIT 20
        """, (g.user_uuid,))
        budget_based = cursor.fetchall()
        
        # 종합 추천 (챗봇 추천으로도 사용)
        cursor.execute("""
            SELECT * FROM combined_recommendations 
            WHERE user_uuid = %s 
            ORDER BY created_at DESC 
            LIMIT 20
        """, (g.user_uuid,))
        combined = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'recommendations': {
                'location_based': location_based,
                'budget_based': budget_based,
                'combined': combined,
                'chatbot': combined  # 챗봇 추천은 종합 추천과 동일
            },
            'counts': {
                'location_based': len(location_based),
                'budget_based': len(budget_based),
                'combined': len(combined),
                'chatbot': len(combined)
            },
            'message': '모든 추천 매물을 성공적으로 가져왔습니다.'
        })
        
    except Exception as e:
        print(f"전체 추천 오류: {e}")
        return jsonify({
            'success': False,
            'message': f'추천 매물 조회 중 오류가 발생했습니다: {str(e)}'
        }), 500