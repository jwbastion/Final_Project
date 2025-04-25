from playwright.sync_api import sync_playwright
import re
import time
import json


def scroll_to_bottom(page, wait=1.0, max_tries=30):
    """페이지를 스크롤하여 모든 데이터를 로딩"""
    previous_height = 0
    tries = 0

    while tries < max_tries:
        # 현재 높이 측정
        current_height = page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            print("📌 더 이상 새 항목이 없습니다.")
            break

        print(f"🔽 스크롤 시도 {tries+1}...")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(wait)  # 로딩 시간 기다리기
        previous_height = current_height
        tries += 1


def scrape_gobang():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # True로 하면 브라우저 안 뜸
        page = browser.new_page()
        page.goto("https://gobang.kr/one-two")
        page.wait_for_load_state("networkidle")

        # 🔽 모든 항목 로딩될 때까지 스크롤
        # scroll_to_bottom(page, wait=1.5, max_tries=56)

        # 1. 리스트에서 모든 상세 페이지 링크 수집
        src_list = page.eval_on_selector_all(
            "img.center-cropped",  # 제목에 해당하는 링크
            "elements => elements.map(el => el.src)",
        )

        house_links = []
        for src in src_list:
            match = re.search(r"/house/(\d+)/", src)
            if match:
                house_id = match.group(1)
                url = f"https://gobang.kr/place/{house_id}"
                house_links.append(url)

        print(f"총 {len(house_links)}개의 집을 찾았습니다.")

        results = {}
        # 2. 각각의 상세 페이지 방문
        for idx, link in enumerate(house_links):
            print(f"\n[{idx+1}] 상세 페이지: {link}")
            detail_page = browser.new_page()
            detail_page.goto(link)
            detail_page.wait_for_load_state("networkidle")
            detail_page.wait_for_selector(
                "section.house_wrap-block__8ymq2"
            )  # 페이지 진입 후 요소 확실히 로드되도록 대기

            # 3. 필요한 데이터 추출 (예시: 제목, 가격, 주소)
            dl_data = detail_page.evaluate(
                """
                () => {
                    const result = {}
                    
                    const sections = document.querySelectorAll("section.house_wrap-block__8ymq2");
                    for (const section of sections) {
                        const heading = section.querySelector("h2");
                        if (heading && heading.innerText.trim() === "매물정보") {
                            const dls = section.querySelectorAll("dl");
                            
                            for (const dl of dls) {
                                const dt = dl.querySelector("dt")?.innerText.trim();
                                const dd = dl.querySelector("dd")?.innerText.trim().replace(/\\s+/g, " ");
                                if (dt && dd) {
                                    result[dt] = dd
                                }
                            }
                            break
                        }
                    }
                    
                    // 2. 주소
                    const addrEl = document.querySelector("div.house_name__d_yZc");
                    if (addrEl) {
                        result["주소"] = addrEl.innerText.trim();
                    }

                    // 3. 근처역 정보
                    const subwayEl = document.querySelector("div.house_txt-naer-info__EuNE2");
                    if (subwayEl) {
                        result["근처 지하철역"] = subwayEl.innerText.trim();
                    }

                    return result;
                }
        """
            )

            results[link] = dl_data
            detail_page.close()

        with open("매물정보.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print("\n✅ 저장 완료: 매물정보.json")

        browser.close()


if __name__ == "__main__":
    scrape_gobang()
