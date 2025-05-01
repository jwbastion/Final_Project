# 🗂️ PostgreSQL + pgAdmin 사용 가이드
---

## 🐳 1. Docker로 서버 실행

루트 디렉토리 (`Final_Project/`)에서 아래 명령어를 실행

```bash
docker compose up --build
```

> 종료 시에는 `Ctrl+C` 또는 별도로 `docker compose down`을 실행하세요.

---

## 🔑 2. pgAdmin 접속 방법

1. 브라우저에서 다음 주소로 접속:
   ```
   http://<서버IP>:8080
   예: http://172.16.220.246:8080
   ```

2. 로그인 정보:

| 항목       | 값             |
|------------|----------------|
| Email      | admin@admin.com |
| Password   | admin1234       |

3. 새 서버 등록:

| 설정 항목           | 값                     |
|--------------------|------------------------|
| Name               | zipup_db               |
| Host name/address  | ****                   |
| Port               | 5432                   |
| Maintenance DB     | postgres               |
| Username           |                |
| Password           |             |

> 연결 후 `Databases > zipup_db > Schemas > public > Tables` 에서 테이블 목록 확인 가능

---

## 🧾 3. 생성된 주요 테이블 정보

| 테이블명 | 설명 |
|----------|------|
| `users` | 사용자 정보 (email, password) |
| `officetels` | 오피스텔 매물 목록 (주소, 가격, 구조 등) |
| `life_mart`, `life_park`, ... | 생활 인프라별 위치 정보 |
| `play_pc_cafe`, `play_karaoke`, `play_cinema` | 여가 관련 장소 |
| `safety_police_station` | 파출소 위치 |
| `traffic_bus`, `traffic_subway` | 교통 관련 인프라 |
| `health_hospital`, `health_pharmacy` | 병원 및 약국 |

---

## 💻 4. Query Tool 사용 예시

### 현재 DB 확인
```sql
SELECT current_database();
```

### 모든 테이블 목록 보기
```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

### 특정 테이블 조회
```sql
SELECT * FROM officetels LIMIT 10;
```

---

## 🔁 5. 참고 명령어

### PostgreSQL 접속 (컨테이너 내부에서)
```bash
docker exec -it zipup_postgres psql -U teammate -d postgres
```

---

## ✅ 6. 기타 참고

- pgAdmin 기본 포트는 `8080`
- PostgreSQL 포트는 `5432`

---

