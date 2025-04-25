from playwright.sync_api import sync_playwright
import json


def save_api_response_json():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 감지할 URL 패턴 (여기에 gobang의 실제 API 패턴을 넣어야 함)
        target_api_url_part = "/www.dabangapp.com/api/v5/region-stat/room"

        captured_data = {}

        def handle_response(response):
            if target_api_url_part in response.url and response.status == 200:
                try:
                    json_data = response.json()
                    captured_data.update(json_data)
                except:
                    pass

        # API 응답 감지
        page.on("response", handle_response)

        # 페이지 이동
        page.goto("https://www.dabangapp.com/map/onetwo")
        page.wait_for_timeout(5000)  # API 응답 대기 시간 (더 늘려도 됨)

        # 저장
        with open("gobang_api_result.json", "w", encoding="utf-8") as f:
            json.dump(captured_data, f, indent=2, ensure_ascii=False)

        print("✅ 저장 완료: gobang_api_result.json")
        browser.close()


save_api_response_json()
