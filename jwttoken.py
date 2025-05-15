import jwt
import datetime

JWT_SECRET = "c784167e8eef4fcbe6f1a01fba80d648f2c8835c18d18f453d9484e785122faf"
JWT_ALGORITHM = "HS256"  
JWT_EXPIRATION = 3600    

payload = {
    "user_uuid": "0faf113d-a93c-4cf6-9754-75407369be9d",
    "email": "33333@naver.com",
    "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=JWT_EXPIRATION)
}

token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
print(token)
