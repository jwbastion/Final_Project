from liveport.models.user_model import Users, db
from datetime import datetime
import hashlib
import pytz


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(email, password, nickname):
    if Users.query.filter_by(email=email).first():
        return None
    hashed_pw = hash_password(password)
    new_user = Users(email=email, password=hashed_pw, nickname=nickname)
    db.session.add(new_user)
    db.session.commit()
    return new_user


def verify_user(email, password):
    hashed_pw = hash_password(password)
    user = Users.query.filter_by(email=email, password=hashed_pw).first()
    if user:
        KST = pytz.timezone("Asia/Seoul")
        user.last_login_at = datetime.utcnow()
        db.session.commit()
    return user
