import time
import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from RAG.api.config import DB_CONFIG


class UserState:
    def __init__(self, user_uuid=None):
        # 기본 상태 설정
        self.state = self._get_default_state()

        # UUID가 제공된 경우 사용자 정보 로드 시도
        if user_uuid:
            self.state["user_uuid"] = user_uuid

            # 먼저 파일에서 로드 시도
            if self._load_from_file(user_uuid):
                print(
                    f"{self.state.get('nickname', '사용자')}님의 정보를 로드했습니다."
                )
            else:
                # 파일에 없으면 DB에서 로드 시도
                try:
                    user_data = self.get_user_by_uuid(user_uuid)
                    if user_data:
                        # 필수 필드만 업데이트 (기존 설정은 유지)
                        essential_fields = {"user_uuid": user_uuid}

                        # 좌표 정보가 있으면 업데이트
                        if (
                            "latitude" in user_data
                            and user_data["latitude"] is not None
                        ):
                            essential_fields["lat"] = float(user_data["latitude"])
                        if (
                            "longitude" in user_data
                            and user_data["longitude"] is not None
                        ):
                            essential_fields["lng"] = float(user_data["longitude"])

                        # 프로필 정보가 있으면 업데이트
                        if "address" in user_data and user_data["address"]:
                            essential_fields["address"] = user_data["address"]
                        if (
                            "preferred_area" in user_data
                            and user_data["preferred_area"]
                        ):
                            essential_fields["preferred_area"] = user_data[
                                "preferred_area"
                            ]
                        if "nickname" in user_data and user_data["nickname"]:
                            essential_fields["nickname"] = user_data["nickname"]

                        # 설정이 완료되었다고 표시
                        essential_fields["setup_complete"] = True

                        # 필수 필드만 업데이트
                        self.state.update(essential_fields)

                        # 예산 정보가 있으면 항상 DB 값으로 업데이트
                        if "budget" in user_data and user_data["budget"] is not None:
                            self.state["rent"] = int(user_data["budget"])
                        if "monthly" in user_data and user_data["monthly"] is not None:
                            self.state["deposit"] = int(user_data["monthly"])
                        if (
                            "maintenance_fee" in user_data
                            and user_data["maintenance_fee"] is not None
                        ):
                            self.state["maint"] = int(user_data["maintenance_fee"])

                        print(
                            f"{self.state.get('nickname', '사용자')}님의 정보를 DB에서 로드했습니다."
                        )
                except Exception as e:
                    print(f"DB에서 사용자 정보 로드 중 오류 발생: {e}")
                    print("기본 설정으로 진행합니다.")

    def _get_default_state(self):
        """기본 사용자 상태 반환"""
        return {
            "user_uuid": None,
            "lat": 37.5055712636346,
            "lng": 126.941856308051,
            "service": None,
            "movement": None,
            "time_limit": None,
            "radius": None,
            "rent": 50,
            "deposit": 1000,
            "maint": 30,
            "infra_preferences": {},
            "infra_details": {},
            "property_features": {},
            "chat_history": [],
            "address": "",
            "preferred_area": "",
            "nickname": "사용자",
        }

    def _get_user_data_dir(self):
        """사용자 데이터 디렉토리 반환"""
        data_dir = "user_data"
        os.makedirs(data_dir, exist_ok=True)
        return data_dir

    def _get_user_file_path(self, user_uuid):
        """사용자 데이터 파일 경로 반환"""
        return os.path.join(self._get_user_data_dir(), f"{user_uuid}.json")

    def _load_from_file(self, user_uuid):
        """파일에서 사용자 데이터 로드"""
        file_path = self._get_user_file_path(user_uuid)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.state.update(data)
                return True
            except Exception as e:
                print(f"파일에서 사용자 데이터 로드 중 오류: {e}")
        return False

    def _save_to_file(self):
        """파일에 사용자 데이터 저장"""
        if not self.state.get("user_uuid"):
            return

        file_path = self._get_user_file_path(self.state["user_uuid"])
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            print(f"사용자 데이터를 파일에 저장했습니다: {file_path}")
        except Exception as e:
            print(f"파일에 사용자 데이터 저장 중 오류: {e}")

    def get_user_by_uuid(self, uuid):
        """UUID로 사용자 정보 조회"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            query = """
            SELECT * FROM users 
            WHERE user_uuid = %s
            """

            cursor.execute(query, (uuid,))
            user_data = cursor.fetchone()
            cursor.close()
            conn.close()

            return user_data
        except Exception as e:
            print(f"사용자 정보 조회 오류: {e}")
            return None

    def get(self, key, default=None):
        """상태에서 키에 해당하는 값을 가져옴"""
        return self.state.get(key, default)

    def reset_settings(self, preserve_location_budget=True):
        """사용자 설정 초기화 - 위치 및 예산 정보는 보존 옵션 있음"""
        # 현재 위치 및 예산 정보 백업
        location_budget_backup = {}
        if preserve_location_budget:
            # 중요 필드 백업
            for key in ["lat", "lng", "rent", "deposit", "maint"]:
                if key in self.state:
                    location_budget_backup[key] = self.state[key]

        # 사용자 UUID 보존
        user_uuid = self.state.get("user_uuid")

        # 기본 상태로 초기화
        self.state = self._get_default_state()

        # UUID 복원
        if user_uuid:
            self.state["user_uuid"] = user_uuid

        # 위치 및 예산 정보 복원 (옵션에 따라)
        if preserve_location_budget:
            self.state.update(location_budget_backup)

        # 변경사항 저장
        self._save_to_file()

        # DB에도 변경사항 저장 시도
        if user_uuid:
            try:
                self.save_user_preferences()
                print("초기화된 설정을 DB에 저장했습니다.")
            except Exception as e:
                print(f"초기화된 설정 DB 저장 오류 (무시됨): {e}")

        return True

    # 사용자 입력을 요구하는 함수 대신 이 함수로 대체
    def reset_settings_with_confirmation(self, confirm=False):
        """확인 값을 파라미터로 받아 설정을 초기화하는 함수"""
        if confirm:
            # 위치 및 예산 정보는 항상 보존
            result = self.reset_settings(preserve_location_budget=True)
            print("위치 및 예산 정보를 제외한 설정이 초기화되었습니다.")
            return result
        else:
            print("설정이 유지됩니다.")
            return False

    def update(self, key, value):
        """상태 업데이트"""
        if key.startswith("infra_detail_"):
            parts = key.split(
                "_", 3
            )  # infra_detail_traffic_subway_0 -> ['infra', 'detail', 'traffic', 'subway_0']

            if len(parts) >= 4:
                # 인프라 타입 (traffic_subway)과 질문 인덱스(0) 추출
                infra_type = parts[2] + "_" + parts[3].split("_")[0]  # traffic_subway

                try:
                    question_idx = int(parts[3].split("_")[1]) if "_" in parts[3] else 0
                except (ValueError, IndexError):
                    question_idx = 0

                if "infra_details" not in self.state:
                    self.state["infra_details"] = {}
                if infra_type not in self.state["infra_details"]:
                    self.state["infra_details"][infra_type] = {}

                self.state["infra_details"][infra_type][question_idx] = value
            else:
                # 형식이 맞지 않으면 그냥 저장
                self.state[key] = value
        elif key.startswith("feature_"):
            feature_code = key.split("_")[1]
            if "property_features" not in self.state:
                self.state["property_features"] = {}
            self.state["property_features"][feature_code] = value
        else:
            self.state[key] = value

        # 변경 사항을 파일에 저장
        self._save_to_file()

        # DB에 저장 시도 (중요 필드만)
        if self.state.get("user_uuid") and key in [
            "rent",
            "deposit",
            "maint",
            "preferred_area",
            "lat",
            "lng",
        ]:
            try:
                self.save_user_preferences()
            except Exception as e:
                print(f"사용자 선호도 DB 저장 오류 (무시됨): {e}")

    def save_user_preferences(self):
        """사용자 선호도 DB에 저장"""
        if not self.state.get("user_uuid"):
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 열 이름에 따라 동적으로 쿼리 구성
            update_parts = []
            params = []

            field_mapping = {
                "budget": "rent",
                "monthly": "deposit",
                "maintenance_fee": "maint",
                "preferred_area": "preferred_area",
                "latitude": "lat",
                "longitude": "lng",
            }

            for db_col, state_key in field_mapping.items():
                if state_key in self.state:
                    update_parts.append(f"{db_col} = %s")
                    params.append(self.state[state_key])

            if not update_parts:
                print("업데이트할 열이 없습니다.")
                cursor.close()
                conn.close()
                return

            # 파라미터에 UUID 추가
            params.append(self.state["user_uuid"])

            # 최종 쿼리 구성
            query = f"""
            UPDATE users 
            SET {', '.join(update_parts)}
            WHERE user_uuid = %s
            """

            cursor.execute(query, params)

            conn.commit()
            cursor.close()
            conn.close()
            print("DB에 사용자 선호도 저장 완료")

        except Exception as e:
            print(f"사용자 선호도 저장 오류: {e}")

    def add_to_history(self, user_message, bot_response):
        """대화 기록 추가"""
        print(f"대화 기록 추가 시도: 사용자 메시지: '{user_message[:30]}...'")

        # chat_history가 없으면 초기화
        if "chat_history" not in self.state:
            self.state["chat_history"] = []

        # 메모리에 대화 기록 추가
        self.state["chat_history"].append(
            {"user": user_message, "bot": bot_response, "timestamp": time.time()}
        )

        # 파일에 저장
        self._save_to_file()

        # DB에 저장 시도
        if self.state.get("user_uuid"):
            try:
                result = self.save_chat_history(user_message, bot_response)
                if result:
                    print(
                        f"대화 기록이 DB에 성공적으로 저장되었습니다. (UUID: {self.state.get('user_uuid')[:8]}...)"
                    )
                else:
                    print("대화 기록 DB 저장 실패")
            except Exception as e:
                print(f"대화 기록 DB 저장 오류 (무시됨): {e}")
        else:
            print("user_uuid가 없어 DB 저장을 건너뜁니다.")

    def save_chat_history(self, user_message, bot_response):
        """대화 기록 DB에 저장"""
        if not self.state.get("user_uuid"):
            print("user_uuid가 없어 DB 저장을 건너뜁니다.")
            return False

        try:
            print(
                f"DB 연결 시도: {DB_CONFIG.get('host')}:{DB_CONFIG.get('port')}/{DB_CONFIG.get('database')}"
            )
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 테이블 존재 여부 확인
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'chat_history'
                );
            """
            )

            table_exists = cursor.fetchone()[0]

            if not table_exists:
                # 테이블 생성
                create_query = """
                CREATE TABLE chat_history (
                    id SERIAL PRIMARY KEY,
                    user_uuid VARCHAR(255) NOT NULL,
                    message TEXT,
                    response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """

                cursor.execute(create_query)
                conn.commit()
                print("chat_history 테이블을 생성했습니다.")

            # 쿼리 실행
            query = """
            INSERT INTO chat_history (user_uuid, message, response, created_at)
            VALUES (%s, %s, %s, NOW())
            """

            cursor.execute(
                query, (self.state.get("user_uuid"), user_message, bot_response)
            )

            conn.commit()
            cursor.close()
            conn.close()
            print("DB에 대화 기록 저장 완료")
            return True

        except Exception as e:
            print(f"대화 기록 저장 오류 (상세): {str(e)}")
            # 스택 트레이스 출력
            import traceback

            traceback.print_exc()
            return False

    def get_history(self, limit=5):
        """최근 대화 기록 반환"""
        if "chat_history" not in self.state:
            return []
        return self.state["chat_history"][-limit:]

    def save_recommendations_to_db(self, recommendations):
        """추천 매물을 DB에 저장"""
        if not self.state.get("user_uuid"):
            print("사용자 UUID가 없어 DB에 저장할 수 없습니다.")
            return False

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # 테이블 존재 여부 확인 및 생성
            for table in [
                "combined_recommendations",
                "location_recommendations",
                "budget_recommendations",
            ]:
                cursor.execute(
                    f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{table}'
                    );
                """
                )

                table_exists = cursor.fetchone()[0]

                if not table_exists:
                    # 테이블 생성
                    if table == "combined_recommendations":
                        create_query = f"""
                            CREATE TABLE {table} (
                                id SERIAL PRIMARY KEY,
                                user_uuid VARCHAR(255) NOT NULL,
                                property_id VARCHAR(255) NOT NULL,
                                address TEXT,
                                station VARCHAR(255),
                                rent DOUBLE PRECISION,
                                deposit DOUBLE PRECISION,
                                maint DOUBLE PRECISION,
                                floor VARCHAR(50),
                                heating_type VARCHAR(50),
                                parking BOOLEAN,
                                facilities TEXT,
                                view TEXT,
                                lat DOUBLE PRECISION,
                                lng DOUBLE PRECISION,
                                infra_score DOUBLE PRECISION,
                                time_info TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """
                    else:
                        create_query = f"""
                            CREATE TABLE {table} (
                                id SERIAL PRIMARY KEY,
                                user_uuid VARCHAR(255) NOT NULL,
                                property_id VARCHAR(255) NOT NULL,
                                address TEXT,
                                station VARCHAR(255),
                                rent DOUBLE PRECISION,
                                deposit DOUBLE PRECISION,
                                maint DOUBLE PRECISION,
                                lat DOUBLE PRECISION,
                                lng DOUBLE PRECISION,
                                infra_score DOUBLE PRECISION,
                                time_info TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """

                    cursor.execute(create_query)
                    conn.commit()
                    print(f"{table} 테이블을 생성했습니다.")

            # 기존 추천 결과 삭제
            for table in [
                "combined_recommendations",
                "location_recommendations",
                "budget_recommendations",
            ]:
                cursor.execute(
                    f"DELETE FROM {table} WHERE user_uuid = %s",
                    (self.state["user_uuid"],),
                )

            conn.commit()
            print("기존 추천 결과를 삭제했습니다.")

            # 데이터 저장 함수
            def save_properties(table_name, properties):
                if not properties:
                    return 0

                count = 0
                for prop in properties:
                    try:
                        if table_name == "combined_recommendations":
                            query = f"""
                                INSERT INTO {table_name}
                                (user_uuid, property_id, address, station, rent, deposit, maint,
                                floor, heating_type, parking, facilities, view, lat, lng, infra_score, time_info)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """

                            prop_id = str(hash(str(prop.get("address", ""))))
                            cursor.execute(
                                query,
                                (
                                    self.state["user_uuid"],
                                    prop_id,
                                    prop.get("address", ""),
                                    prop.get("station", ""),
                                    prop.get("rent", 0),
                                    prop.get("deposit", 0),
                                    prop.get("maint", 0),
                                    prop.get("floor", ""),
                                    prop.get("heating_type", ""),
                                    prop.get("parking", False),
                                    prop.get("facilities", ""),
                                    prop.get("view", ""),
                                    prop.get("lat", 0),
                                    prop.get("lng", 0),
                                    prop.get("infra_score", 0),
                                    prop.get("time_info", ""),
                                ),
                            )
                        else:
                            query = f"""
                                INSERT INTO {table_name}
                                (user_uuid, property_id, address, station, rent, deposit, maint,
                                lat, lng, infra_score, time_info)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """

                            prop_id = str(hash(str(prop.get("address", ""))))
                            cursor.execute(
                                query,
                                (
                                    self.state["user_uuid"],
                                    prop_id,
                                    prop.get("address", ""),
                                    prop.get("station", ""),
                                    prop.get("rent", 0),
                                    prop.get("deposit", 0),
                                    prop.get("maint", 0),
                                    prop.get("lat", 0),
                                    prop.get("lng", 0),
                                    prop.get("infra_score", 0),
                                    prop.get("time_info", ""),
                                ),
                            )

                        count += 1
                    except Exception as e:
                        print(f"개별 매물 저장 오류 (무시됨): {e}")
                        continue

                return count

            # 각 테이블에 데이터 저장
            combined_count = save_properties(
                "combined_recommendations", recommendations.get("combined", [])
            )
            location_count = save_properties(
                "location_recommendations", recommendations.get("location_based", [])
            )
            budget_count = save_properties(
                "budget_recommendations", recommendations.get("budget_based", [])
            )

            conn.commit()
            cursor.close()
            conn.close()

            print(
                f"DB에 저장 완료: 종합 {combined_count}개, 위치기반 {location_count}개, 예산기반 {budget_count}개"
            )
            return True

        except Exception as e:
            print(f"추천 매물 DB 저장 오류: {e}")
            return False
