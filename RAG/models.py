import time

class UserState:
    def __init__(self):
        self.state = {
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
            "chat_history": []
        }
    
    def update(self, key, value):
        self.state[key] = value
    
    def get(self, key, default=None):
        return self.state.get(key, default)
    
    def add_to_history(self, user_message, bot_response):
        self.state["chat_history"].append({
            "user": user_message,
            "bot": bot_response,
            "timestamp": time.time()
        })
    
    def get_history(self, limit=5):
        return self.state["chat_history"][-limit:]
