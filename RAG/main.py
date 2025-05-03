from cli import (
    ask_location,
    ask_service_choice,
    handle_transport_flow,
    handle_radius_flow,
    filter_rooms_by_budget,
    filter_radius_rooms_by_budget  
)

from budget import ask_budget_tail

def main():
    user_lat, user_lng = ask_location()

    if str(user_lat).lower() == "exit" or str(user_lng).lower() == "exit":
        print("프로그램을 종료합니다.")
        return

    choice = ask_service_choice()

    if choice.lower() == "exit":
        print("프로그램을 종료합니다.")
        return

    if choice == "1":
        filtered_rooms = handle_transport_flow(user_lat, user_lng)
        if not filtered_rooms:
            return

        print("\n예산 질문으로 넘어갑니다.")
        user_budget = ask_budget_tail()
        final = filter_rooms_by_budget(filtered_rooms, user_budget)

        if not final:
            print("\n❌ 시간 + 예산 조건을 모두 만족하는 매물이 없습니다.")
            return

        print(f"\n💡 최종 추천 매물 {len(final)}건:")
        for r, t, m in final:
            print(f"- {r[2]} / {r[3]} ({r[4]}) | 월세 {r[5]} / 보증금 {r[6]} / 관리비 {r[7]} | {m}로 {t:.1f}분")

    elif choice == "2":
        rooms = handle_radius_flow(user_lat, user_lng)
        if not rooms:
            return

        print("\n예산 질문으로 넘어갑니다.")
        user_budget = ask_budget_tail()

        final = filter_radius_rooms_by_budget(rooms, user_budget)

        if not final:
            print("\n예산 조건을 만족하는 매물이 없습니다.")
            return

        print(f"\n💡 추천 매물 {len(final)}건:")
        for r in final:
            print(f"- {r[2]} / {r[3]} ({r[4]}) | 거리 {r[5]}m | 월세 {r[6]} / 보증금 {r[7]} / 관리비 {r[8]}")

    else:
        print("입력 오류: 1 또는 2를 선택해주세요.")
        return

if __name__ == "__main__":
    main()