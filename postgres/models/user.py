from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    nickname = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    last_login_at = Column(DateTime)
    budget_min = Column(Integer)
    budget_max = Column(Integer)
    preferred_area = Column(Text)

    chat_histories = relationship("ChatHistory", back_populates="user")
    recommendations = relationship("RecommendationResult", back_populates="user")
