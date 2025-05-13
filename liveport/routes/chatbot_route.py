from flask import Blueprint, request, jsonify
from chatbot import RealEstateChatbot
from models import Users

chatbot_bp = Blueprint("chatbot", __name__)
chatbot = RealEstateChatbot()

@chatbot_bp.route("/chatbot", methods=["POST"])
def chatbot_api():
    data = request.get_json()
    email = data.get("email")
    message = data.get("message")

    if not email or not message:
        return jsonify({"error": "email과 message는 필수입니다."}), 400

    user = Users.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

    # 사용자 정보를 chatbot 내부 상태에 전달
    chatbot.user_state.set_user_info({
        "email": user.email,
        "budget": user.budget,
        "monthly": user.monthly,
        "preferred_area": user.preferred_area,
        "latitude": user.latitude,
        "longitude": user.longitude,
        "address": user.address
    })

    # 챗봇에게 메시지를 전달하고 응답 생성
    response = chatbot.process_message(message)
    return jsonify({"response": response})
