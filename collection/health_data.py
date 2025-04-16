import requests
import pandas as pd

api_key = ""
service = "SebcPostOfficeKor"
base_url = f"http://openapi.seoul.go.kr:8088/{api_key}/json/{service}"
start_index = 1
end_index = 1000

all_rows = []

while True:
    url = f"{base_url}/{start_index}/{end_index}/"
    res = requests.get(url)
    data = res.json()

    try:
        rows = data[service]['row']
        all_rows.extend(rows)
        print(f"{start_index}~{end_index}번까지 수집 완료")
        
        # 다음 요청 범위 설정
        start_index += 1000
        end_index += 1000
    except KeyError:
        print("데이터 수집 종료 또는 오류 발생")
        break

# DataFrame으로 변환 및 저장
df = pd.DataFrame(all_rows)
df.to_csv("new_post_office.csv", index=False, encoding="utf-8-sig")
print("전체 CSV 저장 완료!")
