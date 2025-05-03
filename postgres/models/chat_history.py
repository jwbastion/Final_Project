from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, String, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .base import Base

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    turn = Column(Integer, nullable=False)
    speaker = Column(String, nullable=False)
    role = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant')", name="check_role_valid"),
    )

    user = relationship("User", back_populates="chat_histories")