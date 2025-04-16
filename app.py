from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_from_directory,
    session,
    jsonify,
)
from openai import OpenAI
from dotenv import load_dotenv
import os

app = Flask(__name__)

app.config["SECRET_KEY"] = "2AZSMss3p5QPbcY2hBsJ"

# 환경 변수 로드
load_dotenv()
# OpenAI 클라이언트 생성
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # API 키를 설정하세요

# 임시 데이터 저장소 (실제로는 DB를 사용해야 함)
users = {}  # 사용자 정보를 저장하는 딕셔너리

# 질문 리스트
questions = [
    "교통에 대해 선호하는 사항이 있나요?",
    "편의시설(편의점 등)에 대해 선호하는 사항이 있나요?",
    "안전에 대해 어떤 점을 중요하게 생각하시나요?",
    "건강 관련 시설(병원, 약국 등)에 대해 선호하는 사항이 있나요?",
    "녹지 공간(공원 등)에 대해 선호하는 사항이 있나요?",
    "생활 편의성(마트 등)에 대해 어떤 점을 중요하게 생각하시나요?",
    "여가 시설(노래방 등)에 대해 선호하는 사항이 있나요?",
    "운동 시설(헬스장 등)에 대해 선호하는 사항이 있나요?",
]


# @app.before_request
# def initialize_session():
#     """세션 초기화"""
#     if "answers" not in session:
#         session["answers"] = []
#     if "question_index" not in session:
#         session["question_index"] = 0


@app.route("/")
def home():
    """초기 화면: 로그인/회원가입 버튼 표시"""
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """회원가입 페이지"""
    if request.method == "POST":
        # 폼 데이터 가져오기
        name = request.form["name"]
        username = request.form["username"]
        password = request.form["password"]
        gender = request.form["gender"]
        age = request.form["age"]
        budget = request.form["budget"]
        deal_type = request.form["deal_type"]
        pet = request.form["pet"]
        elevator_preference = request.form["elevatorPreference"]

        # 사용자 데이터 저장 (임시로 딕셔너리에 저장)
        users[username] = {
            "name": name,
            "username": username,
            "password": password,
            "gender": gender,
            "age": age,
            "budget": budget,
            "deal_type": deal_type,
            "pet": pet,
            "elevator_preference": elevator_preference,
        }

        return redirect(url_for("login"))  # 회원가입 완료 후 로그인 페이지로 이동

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """로그인 페이지"""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # 사용자 인증
        user = users.get(username)
        if user and user["password"] == password:
            session["username"] = username  # 세션에 사용자 이름 저장
            return redirect(url_for("chatbot"))  # 로그인 성공 시 챗봇 페이지로 이동

        return render_template(
            "login.html", error="아이디 또는 비밀번호가 올바르지 않습니다."
        )

    return render_template("login.html")


@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():
    # 챗봇 화면으로 이동할 때 세션 데이터 초기화
    if request.method == "GET":
        session["answers"] = []  # 답변 초기화
        session["question_index"] = 0  # 질문 인덱스 초기화

    if request.method == "POST":
        user_message = request.json.get("message")
        question_index = session["question_index"]

        # 사용자의 답변 저장
        if question_index < len(questions):
            session["answers"].append(user_message)

        # 모든 질문 완료 시 종료 메시지 반환
        if question_index >= len(questions):
            answers = session["answers"]
            recommendation_prompt = (
                f"사용자가 아래와 같은 답변을 제공했습니다:\n{answers}\n\n"
                f"사용자의 답변을 바탕으로 조건에 맞는 실제 매물을 추천해주세요."
            )

            # OpenAI API를 사용하여 응답 생성
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 부동산 전문가입니다."},
                    {"role": "user", "content": recommendation_prompt},
                ],
            )

            chatbot_response = response.choices[0].message.content

            return jsonify({"response": chatbot_response, "done": True})

        # 다음 질문 반환
        next_question = questions[question_index]
        session["question_index"] += 1

        return jsonify({"response": next_question, "done": False})

    first_question = questions[0]
    return render_template("chatbot.html", first_question=first_question)


@app.route("/logout")
def logout():
    """로그아웃 기능"""
    session.pop("username", None)  # 세션에서 사용자 이름 제거
    return redirect(url_for("home"))  # 초기 화면으로 이동


if __name__ == "__main__":
    app.run(debug=True)
