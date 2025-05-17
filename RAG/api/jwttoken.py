import jwt
import datetime

JWT_SECRET = "c784167e8eef4fcbe6f1a01fba80d648f2c8835c18d18f453d9484e785122faf"
JWT_ALGORITHM = "HS256"  # config.py와 동일해야 함
JWT_EXPIRATION = 3600  # 1시간

payload = {
    "user_uuid": "a774369d-13d2-4e88-9261-0735e85706fd",
    "email": "twins@lg.com",
    "exp": datetime.datetime.now(datetime.timezone.utc)
    + datetime.timedelta(seconds=JWT_EXPIRATION),
}

token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
print(token)
