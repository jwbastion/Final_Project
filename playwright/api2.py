from playwright.sync_api import sync_playwright
import json
import time

# 로컬 JSON 파일 로딩
with open("scroll_api_with_area.json", "r", encoding="utf-8") as f:
    houses = json.load(f)


def fetch_area_from_detail_pages(houses):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        detail_page = context.new_page()

        for house in houses:
            house_id = house.get("ID")
            if not house_id:
                continue

            url = f"https://gobang.kr/place/{house_id}"
            try:
                detail_page.goto(url, timeout=10000)
                detail_page.wait_for_selector(
                    "section.house_wrap-block__8ymq2", timeout=10000
                )

                # 면적 항목 추출
                info = detail_page.evaluate(
                    """
                    () => {
                        const result = {
                            "주실 방향": null,
                            "주차": null,
                            "난방시설": null,
                            "냉방시설": null,
                            "생활시설": null,
                            "안전시설": null,
                            "엘리베이터": null
                        };
                        
                        const sections = document.querySelectorAll("section.house_wrap-block__8ymq2");
                        for (const section of sections) {
                            const h2 = section.querySelector("h2");
                            if (h2 && h2.innerText.includes("매물정보")) {
                                const dls = section.querySelectorAll("dl");
                                for (const dl of dls) {
                                    const dt = dl.querySelector("dt")?.innerText.trim();
                                    const dd = dl.querySelector("dd")?.innerText.trim();
                                    if (dt === "주실 방향" || dt === "주차") {
                                        result[dt] = dd;
                                    }
                                }
                            }
                            else if (h2 && h2.innerText.includes("시설정보")) {
                                const dls = section.querySelectorAll("dl");
                                for (const dl of dls) {
                                    const dt = dl.querySelector("dt")?.innerText.trim();
                                    const dd = dl.querySelector("dd")?.innerText.trim();
                                    if (dt && dd) {
                                        result[dt] = dd;
                                    }
                                }
                            }
                            else if (h2 && h2.innerText.includes("건물정보")) {
                                const dls = section.querySelectorAll("dl");
                                for (const dl of dls) {
                                    const dt = dl.querySelector("dt")?.innerText.trim();
                                    const dd = dl.querySelector("dd")?.innerText.trim();
                                    if (dt === "엘리베이터") {
                                        result[dt] = dd;
                                    }
                                }
                            }
                        }
                        return result;
                    }
                """
                )

                house["주실 방향"] = info.get("주실 방향")
                house["주차"] = info.get("주차")
                house["난방시설"] = info.get("난방시설")
                house["냉방시설"] = info.get("냉방시설")
                house["생활시설"] = info.get("생활시설")
                house["안전시설"] = info.get("안전시설")
                house["엘리베이터"] = info.get("엘리베이터")

            except Exception as e:
                print(f"❌ ID {house_id} - 오류: {e}")
                house["주실 방향"] = None
                house["주차"] = None
                house["난방시설"] = None
                house["냉방시설"] = None
                house["생활시설"] = None
                house["안전시설"] = None
                house["엘리베이터"] = None

        browser.close()
    return houses


# 실행
updated_data = fetch_area_from_detail_pages(houses)

# 저장
with open("gobang_api.json", "w", encoding="utf-8") as f:
    json.dump(updated_data, f, indent=2, ensure_ascii=False)

print("✅ 완료: gobang_api.json")
