# 최상위 app.py
from liveport import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
