# 프로젝트 루트에 server.py 생성
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 임시 사용자 저장소
users = {}


@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if email in users:
        return jsonify({"success": False, "message": "User already exists"}), 400

    users[email] = password
    return jsonify({"success": True})


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if email not in users or users[email] != password:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
