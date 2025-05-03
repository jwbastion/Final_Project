import re

def extract_max_value(text):
    text = text.replace("만원", "").replace("원", "").replace(",", "")
    numbers = re.findall(r'\d{1,6}', text)
    if not numbers:
        return None
    return max(map(int, numbers))

def classify_response(text):
    text = text.lower()
    if any(kw in text for kw in ["모르", "아니", "관심없", "별로", "싫", "그건 좀"]):
        return "negative"
    elif any(kw in text for kw in ["무조건", "꼭", "중요", "상관없", "좋아", "괜찮", "네", "가능"]):
        return "positive"
    elif any(kw in text for kw in ["있으면", "애매", "경우", "잘 모르겠", "보고 결정", "글쎄"]):
        return "neutral"
    return "neutral"

def get_numeric_input(prompt):
    while True:
        print(prompt)
        response = input("> ")
        value = extract_max_value(response)
        if value:
            return value
        print("대략적인 금액이라도 괜찮아요! 예: 50만 원")

def follow_up_limit_dynamic(base_value, category):
    if category == "rent":
        suggested = base_value + 10
        msg = f"월세 {base_value}만 원 정도로 생각하고 계시는군요.\n만약 지하철역 가까운 위치거나 옵션이 잘 갖춰져 있다면 {suggested}만 원까지도 괜찮으실까요?"
    elif category == "deposit":
        suggested = int(round(base_value * 1.5 / 100)) * 100  
        msg = f"보증금은 {base_value}만 원 정도로 계획하고 계시는군요.\n집 상태나 위치가 마음에 들면 {suggested}만 원까지도 괜찮으실까요?"
    elif category == "maintenance":
        suggested = base_value + 3
        msg = f"관리비는 {base_value}만 원 정도로 생각 중이시군요.\n세탁기나 에어컨 등 옵션이 잘 갖춰져 있다면 {suggested}만 원까지도 괜찮으실까요?"
    else:
        suggested = base_value
        msg = f"{base_value}만 원 정도로 입력하셨습니다.\n혹시 조금 더 여유 있는 예산도 가능하실까요?"

    print(msg)
    response = input("> ")
    attitude = classify_response(response)

    if attitude in ["positive", "neutral"]:
        print("그렇다면 최대 어느 정도까지 괜찮으실까요?")
        max_input = input("> ")
        return extract_max_value(max_input) or suggested
    else:
        print("넵, 말씀하신 금액 기준으로 맞춰드릴게요!")
        return base_value

def ask_budget_tail():
    print("\n📌 먼저 예산에 대해 간단히 여쭤볼게요 :)")

    rent = get_numeric_input("Q1. 월세는 어느 정도까지 괜찮으세요?\n예: 40만 원, 50~60만 원 정도도 좋아요.")
    max_rent = follow_up_limit_dynamic(rent, "rent")

    deposit = get_numeric_input("\nQ2. 보증금은 어느 정도까지 생각하고 계세요?\n예: 500만 원, 1000~1500만 원 등")
    max_deposit = follow_up_limit_dynamic(deposit, "deposit")

    maintenance = get_numeric_input("\nQ3. 관리비는 어느 정도까지 괜찮으세요?\n예: 5만 원, 7~10만 원도 괜찮아요.")
    max_maintenance = follow_up_limit_dynamic(maintenance, "maintenance")

    return {
        "rent": rent,
        "max_rent": max_rent,
        "deposit": deposit,
        "max_deposit": max_deposit,
        "maintenance": maintenance,
        "max_maintenance": max_maintenance
    }
