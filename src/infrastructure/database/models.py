from sqlalchemy import Column, String, DateTime, Text, Enum, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class NotificationLog(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False)
    channel = Column(Enum("email", "sms", "display", "telegram", "log", name="channel_types"), nullable=False)
    status = Column(Enum("success", "failed", name="status_types"), nullable=False)
    message = Column(Text, nullable=True)   # nội dung thông báo đã gửi
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    severity = Column(String(20), nullable=True)
    error_detail = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Index để truy vấn nhanh theo event_id và user_id
    __table_args__ = (
        Index("ix_notifications_event_user", "event_id", "user_id"),
    )
    
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    telegram_chat_id = Column(String(255), nullable=True)
    role = Column(Enum("admin", "security_team", "staff", name="role_types"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)