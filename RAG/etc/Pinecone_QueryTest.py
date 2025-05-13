import os
from dotenv import load_dotenv
from pinecone import Pinecone

# 1. 환경 변수 로드
load_dotenv()
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX_NAME"))

# 2. 총 벡터 수 확인
stats = index.describe_index_stats()
total = stats.total_vector_count
print(f"📦 총 벡터 수: {total}개")

# 3. 필수 키 리스트
required_keys = [
    "id", "type", "자치구", "법정동", "address", "rent", "deposit", "maint", "size",
    "direction", "floor", "walk_time", "transit_time", "station", "subway_time",
    "lat", "lng", "주차", "난방", "엘리베이터", "생활시설", "안전시설"
]

# 4. 누락 검사
batch_size = 100
missing_report = []

for start in range(0, total, batch_size):
    ids = [str(i) for i in range(start, min(start + batch_size, total))]
    response = index.fetch(ids=ids)

    for vector_id, vector_data in response.vectors.items():
        metadata = vector_data.metadata
        missing = [key for key in required_keys if key not in metadata]
        if missing:
            missing_report.append((vector_id, missing))

# 5. 결과 출력
if missing_report:
    print("\n❌ 누락된 메타데이터가 있는 벡터 목록:")
    for vid, keys in missing_report:
        print(f"ID: {vid} → 누락: {keys}")
    print(f"\n총 {len(missing_report)}개 벡터에서 누락 발생")
else:
    print("\n✅ 모든 벡터가 필수 메타데이터를 포함하고 있습니다!")
