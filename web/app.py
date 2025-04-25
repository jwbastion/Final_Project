from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = "your_secret_key"

# 메모리 상 사용자 정보 저장용 딕셔너리
users = {}  # 예: { "test@example.com": "password123" }


@app.route("/")
def index():
    return render_template("survey.html")


@app.route("/chatbot")
def chat():
    return render_template("chat.html")


# @app.route("/", methods=["GET", "POST"])
# def index():
#     message = ""
#     show_form = "login"  # 기본으로 로그인 폼 보이기

#     if request.method == "POST":
#         if request.form.get("form_type") == "login":
#             email = request.form.get("email")
#             password = request.form.get("password")

#             if email in users and users[email]["password"] == password:
#                 session["user"] = email
#                 message = "Login successful!"
#             else:
#                 message = "Invalid email or password."
#                 show_form = "login"

#         elif request.form.get("form_type") == "signup":
#             email = request.form.get("email")
#             password = request.form.get("password")
#             confirm = request.form.get("confirm")
#             age = request.form.get("age")
#             gender = request.form.get("gender")
#             budget = request.form.get("budget")
#             preference = request.form.get("preference")

#             if email in users:
#                 message = "Email already registered."
#                 show_form = "signup"
#             elif password != confirm:
#                 message = "Passwords do not match."
#                 show_form = "signup"
#             else:
#                 users[email] = {
#                     "password": password,
#                     "age": age,
#                     "gender": gender,
#                     "budget": budget,
#                     "preference": preference,
#                 }
#                 message = "Signup successful! You can now log in."
#                 show_form = "login"

#     return render_template(
#         "index.html", message=message, show_form=show_form, user=session.get("user")
#     )


# @app.route("/chatbot")
# def chatbot():
#     if "user_email" not in session:
#         return redirect(url_for("index"))
#     return render_template("chatbot.html", user_email=session.get("user"))


# @app.route("/chat", methods=["POST"])
# def chat():
#     user_message = request.json.get("message", "")

#     # 간단한 응답 예시
#     if "안녕" in user_message:
#         reply = "안녕하세요! 😊"
#     elif "매물" in user_message:
#         reply = "원하시는 지역이나 예산을 말씀해 주세요!"
#     else:
#         reply = f"'{user_message}'에 대한 답변은 아직 준비 중이에요!"

#     return jsonify({"reply": reply})


# @app.route("/logout")
# def logout():
#     # session.pop("user", None)
#     session.pop("user", None)
#     return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
