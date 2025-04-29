from cli import ask_location, ask_service_choice, handle_transport_flow, handle_radius_flow

def main():
    user_lat, user_lng = ask_location()
    choice = ask_service_choice()

    if choice == "1":
        handle_transport_flow(user_lat, user_lng)
    elif choice == "2":
        handle_radius_flow(user_lat, user_lng)
    else:
        print("잘못된 입력입니다.")

if __name__ == "__main__":
    main()
