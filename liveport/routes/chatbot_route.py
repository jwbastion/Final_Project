from flask import Blueprint, request, jsonify, g, Response
from liveport.services.auth_service import token_required
from liveport.services.chatbot_service import RealEstateChatbot
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import current_app
import datetime

chatbot_bp = Blueprint("chatbot", __name__)


# 데이터베이스 연결 유틸리티 함수
def get_db_connection():
    conn = psycopg2.connect(**current_app.config["DB_CONFIG"])
    conn.set_client_encoding("UTF8")
    return conn


@chatbot_bp.route("/reset", methods=["OPTIONS"])
def reset_chat_options():
    return "", 200


@chatbot_bp.route("/reset", methods=["POST"])
@token_required
def reset_chat():
    try:
        user_uuid = g.user_uuid

        # 채팅 이력 삭제
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE user_uuid = %s", (user_uuid,))

        # 사용자 대화 상태 초기화
        cursor.execute(
            "DELETE FROM user_conversation_states WHERE user_uuid = %s", (user_uuid,)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "대화가 초기화되었습니다."}), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"대화 초기화 중 오류: {str(e)}"}),
            500,
        )


# CORS 프리플라이트 요청 처리
@chatbot_bp.route("/message", methods=["OPTIONS"])
def chat_message_options():
    # 빈 응답 반환 (헤더는 app.py의 after_request에서 추가됨)
    return "", 200


# 채팅 메시지 처리 API
@chatbot_bp.route("/message", methods=["POST"])
@token_required
def chat_message():
    data = request.get_json()

    if not data or not data.get("message"):
        return jsonify({"success": False, "message": "메시지를 입력하세요!"}), 400

    try:
        user_uuid = g.user_uuid
        chatbot = RealEstateChatbot(user_uuid)
        response = chatbot.process_message(data.get("message"))

        # 대화 이력 저장
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO chat_history (user_uuid, message, response, created_at) VALUES (%s, %s, %s, NOW())",
                (user_uuid, data.get("message"), response),
            )
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as db_error:
            print(f"대화 이력 저장 오류 (무시): {db_error}")

        response_obj = jsonify({"success": True, "response": response})
        response_obj.headers["Content-Type"] = "application/json; charset=utf-8"
        return response_obj, 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"메시지 처리 중 오류: {str(e)}"}),
            500,
        )


# CORS 프리플라이트 요청 처리
@chatbot_bp.route("/history", methods=["OPTIONS"])
def chat_history_options():
    return "", 200


@chatbot_bp.route("/history", methods=["GET"])
@token_required
def get_chat_history():
    limit = int(request.args.get("limit", 20))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM chat_history WHERE user_uuid = %s ORDER BY created_at DESC LIMIT %s",
            (g.user_uuid, limit),
        )
        history = cursor.fetchall()
        cursor.close()
        conn.close()

        # 한글 인코딩 문제 해결을 위한 처리
        history_list = []
        for entry in history:
            entry_dict = dict(entry)
            if isinstance(entry_dict.get("created_at"), datetime.datetime):
                entry_dict["created_at"] = entry_dict["created_at"].isoformat()
            history_list.append(entry_dict)

        response = jsonify({"success": True, "history": history_list})

        response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response, 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"채팅 이력 조회 중 오류: {str(e)}"}),
            500,
        )


# 위치 기반 추천 API
@chatbot_bp.route("/recommendations/location", methods=["GET"])
@token_required
def get_location_recommendations():
    try:
        lat = request.args.get("lat")
        lng = request.args.get("lng")
        radius = int(request.args.get("radius", "1000"))
        limit = int(request.args.get("limit", "10"))

        # 위치 파라미터 필수 체크
        if not lat or not lng:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT latitude, longitude FROM users WHERE user_uuid = %s",
                (g.user_uuid,),
            )
            user_location = cursor.fetchone()
            cursor.close()
            conn.close()

            if (
                user_location
                and user_location.get("latitude")
                and user_location.get("longitude")
            ):
                lat = user_location["latitude"]
                lng = user_location["longitude"]
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "위치 정보가 필요합니다. 위도(lat)와 경도(lng)를 제공하거나 사용자 설정에 저장하세요.",
                        }
                    ),
                    400,
                )

        # 거리 기반 매물 검색
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT *, 
                6371 * 2 * asin(sqrt(power(sin(radians(%s - latitude) / 2), 2) + 
                                    cos(radians(%s)) * cos(radians(latitude)) * 
                                    power(sin(radians(%s - longitude) / 2), 2))) * 1000 as distance
            FROM officetels
            WHERE 6371 * 2 * asin(sqrt(power(sin(radians(%s - latitude) / 2), 2) + 
                                    cos(radians(%s)) * cos(radians(latitude)) * 
                                    power(sin(radians(%s - longitude) / 2), 2))) * 1000 <= %s
            ORDER BY distance
            LIMIT %s
        """,
            (lat, lat, lng, lat, lat, lng, radius, limit),
        )

        properties = cursor.fetchall()
        cursor.close()
        conn.close()

        return (
            jsonify(
                {
                    "success": True,
                    "properties": properties,
                    "count": len(properties),
                    "params": {"lat": lat, "lng": lng, "radius": radius},
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"거리 기반 추천 중 오류: {str(e)}"}),
            500,
        )


# 예산 기반 추천 API
@chatbot_bp.route("/recommendations/budget", methods=["GET"])
@token_required
def get_budget_recommendations():
    try:
        monthly = request.args.get("monthly")
        deposit = request.args.get("deposit")
        maintenance = request.args.get("maintenance")
        limit = int(request.args.get("limit", "10"))

        # 예산 파라미터가 없으면 사용자 설정에서 가져오기
        if not monthly or not deposit or not maintenance:
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT budget, monthly, maintenance_fee FROM users WHERE user_uuid = %s",
                (g.user_uuid,),
            )
            user_budget = cursor.fetchone()
            cursor.close()
            conn.close()

            if user_budget:
                monthly = monthly or user_budget.get("budget", 50)
                deposit = deposit or user_budget.get("monthly", 1000)
                maintenance = maintenance or user_budget.get("maintenance_fee", 10)
            else:
                monthly = monthly or 50
                deposit = deposit or 1000
                maintenance = maintenance or 10

        # 예산 기반 매물 검색
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT * FROM officetels
            WHERE monthly_rent <= %s AND deposit <= %s AND maintenance_fee <= %s
            ORDER BY (monthly_rent + deposit/100) ASC
            LIMIT %s
        """,
            (monthly, deposit, maintenance, limit),
        )

        properties = cursor.fetchall()
        cursor.close()
        conn.close()

        return (
            jsonify(
                {
                    "success": True,
                    "properties": properties,
                    "count": len(properties),
                    "params": {
                        "monthly": monthly,
                        "deposit": deposit,
                        "maintenance": maintenance,
                    },
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"예산 기반 추천 중 오류: {str(e)}"}),
            500,
        )


# 챗봇 추천 API
@chatbot_bp.route("/recommendations/chatbot", methods=["GET"])
@token_required
def get_chatbot_recommendations():
    try:
        chatbot = RealEstateChatbot(g.user_uuid)
        recommendations = chatbot.recommender.get_recommendations()

        if (
            not recommendations.get("combined")
            and not recommendations.get("location_based")
            and not recommendations.get("budget_based")
        ):
            return (
                jsonify(
                    {
                        "success": True,
                        "has_recommendations": False,
                        "message": "설정하신 조건에 맞는 매물을 찾지 못했습니다. 조건을 변경해보세요.",
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "success": True,
                    "has_recommendations": True,
                    "combined": recommendations.get("combined", [])[:5],
                    "location_based": recommendations.get("location_based", [])[:3],
                    "budget_based": recommendations.get("budget_based", [])[:3],
                }
            ),
            200,
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"챗봇 추천 중 오류: {str(e)}"}),
            500,
        )


# CORS 프리플라이트 요청 처리
@chatbot_bp.route("/favorites", methods=["OPTIONS"])
def favorites_options():
    return "", 200


# 관심 매물 관리 API
@chatbot_bp.route("/favorites", methods=["POST"])
@token_required
def add_favorite():
    data = request.get_json()

    if not data or not data.get("property_id"):
        return jsonify({"success": False, "message": "매물 ID를 입력하세요!"}), 400

    property_id = str(data.get("property_id"))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # 이미 즐겨찾기에 있는지 확인 (UNIQUE 제약조건 활용)
        cursor.execute(
            "SELECT COUNT(*) FROM favorite_properties WHERE user_uuid = %s AND property_id = %s",
            (g.user_uuid, property_id),
        )

        count = cursor.fetchone()["count"]

        if count > 0:
            return (
                jsonify(
                    {"success": False, "message": "이미 관심 매물로 등록되어 있습니다."}
                ),
                400,
            )

        # 매물 정보는 추천 테이블에서 가져오기
        property_data = None

        for table in [
            "budget_recommendations",
            "location_recommendations",
            "combined_recommendations",
        ]:
            cursor.execute(
                f"SELECT * FROM {table} WHERE property_id = %s AND user_uuid = %s LIMIT 1",
                (property_id, g.user_uuid),
            )
            property_data = cursor.fetchone()
            if property_data:
                break

        if not property_data:
            return (
                jsonify(
                    {"success": False, "message": "해당 매물 정보를 찾을 수 없습니다."}
                ),
                404,
            )

        # 모든 매물 정보를 favorite_properties 테이블에 저장 (id는 자동증가)
        cursor.execute(
            """INSERT INTO favorite_properties (
                user_uuid, property_id, address, station, rent, deposit, maint, 
                floor, heating_type, parking, facilities, view, lat, lng, 
                infra_score, time_info, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id""",
            (
                g.user_uuid,
                property_id,
                property_data.get("address", ""),
                property_data.get("station", ""),
                property_data.get("rent", 0),
                property_data.get("deposit", 0),
                property_data.get("maint", 0),
                property_data.get("floor", ""),
                property_data.get("heating_type", ""),
                property_data.get("parking", False),
                property_data.get("facilities", ""),
                property_data.get("view", ""),
                property_data.get("lat", 0.0),
                property_data.get("lng", 0.0),
                property_data.get("infra_score", 0.0),
                property_data.get("time_info", ""),
            ),
        )

        # 생성된 ID 가져오기
        favorite_id = cursor.fetchone()["id"]

        conn.commit()
        cursor.close()
        conn.close()

        return (
            jsonify(
                {
                    "success": True,
                    "message": "관심 매물로 등록되었습니다.",
                    "favorite_id": favorite_id,
                }
            ),
            201,
        )

    except Exception as e:
        print(f"관심 매물 등록 오류: {e}")
        if "duplicate key value violates unique constraint" in str(e):
            return (
                jsonify(
                    {"success": False, "message": "이미 관심 매물로 등록되어 있습니다."}
                ),
                400,
            )
        return (
            jsonify({"success": False, "message": f"관심 매물 등록 중 오류: {str(e)}"}),
            500,
        )


@chatbot_bp.route("/favorites/list", methods=["GET"])
@token_required
def list_favorites():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute(
            "SELECT property_id FROM favorite_properties WHERE user_uuid = %s",
            (g.user_uuid,),
        )
        rows = cursor.fetchall()

        conn.close()
        return jsonify({"success": True, "favorites": rows}), 200

    except Exception as e:
        print(f"관심 목록 불러오기 오류: {e}")
        return (
            jsonify({"success": False, "message": "관심 목록 조회 중 오류 발생"}),
            500,
        )


@chatbot_bp.route("/favorites", methods=["GET"])
@token_required
def get_favorites():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        # LIMIT 제거하여 모든 관심 매물 가져오기
        cursor.execute(
            "SELECT * FROM favorite_properties WHERE user_uuid = %s ORDER BY created_at DESC",
            (g.user_uuid,),
        )
        favorites = cursor.fetchall()
        cursor.close()
        conn.close()

        return (
            jsonify({"success": True, "favorites": favorites, "count": len(favorites)}),
            200,
        )

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"관심 매물 조회 중 오류: {str(e)}"}),
            500,
        )


# CORS 프리플라이트 요청 처리
@chatbot_bp.route("/favorites/<string:favorite_id>", methods=["OPTIONS"])
def favorite_delete_options(favorite_id):
    return "", 200


@chatbot_bp.route("/favorites/<string:favorite_id>", methods=["DELETE"])
@token_required
def delete_favorite(favorite_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM favorite_properties WHERE id = %s AND user_uuid = %s",
            (favorite_id, g.user_uuid),
        )

        if cursor.rowcount == 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "해당 관심 매물을 찾을 수 없거나 접근 권한이 없습니다.",
                    }
                ),
                404,
            )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"success": True, "message": "관심 매물이 삭제되었습니다."}), 200

    except Exception as e:
        return (
            jsonify({"success": False, "message": f"관심 매물 삭제 중 오류: {str(e)}"}),
            500,
        )
