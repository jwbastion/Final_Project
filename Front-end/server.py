# 프로젝트 루트에 server.py 생성
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

# 임시 사용자 저장소
users = {}

DATA_FILE = "survey_responses.json"

def load_responses():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_responses(responses):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)


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


@app.route("/api/survey", methods=["POST"])
def submit_survey():
    data = request.get_json()
    responses = load_responses()
    responses.append(data)  # 새로운 설문 응답 추가
    save_responses(responses)
    return jsonify({"status": "ok"}), 201


@app.route("/api/survey/latest", methods=["GET"])
def get_latest_survey():
    responses = load_responses()
    if not responses:
        return jsonify({}), 404
    return jsonify(responses[-1])  # 마지막 설문 응답 반환

if __name__ == "__main__":
    app.run(debug=True)
