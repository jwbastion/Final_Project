from liveport import create_app
from routes.chatbot_route import chatbot_bp

app = create_app()
app.register_blueprint(chatbot_bp, url_prefix="/api")

if __name__ == '__main__':
    app.run(debug=True)
