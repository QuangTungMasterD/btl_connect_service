import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SERVICE_NAME = os.getenv("SERVICE_NAME", "notification-service")
    SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
    AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")
    
    # RabbitMQ
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
    RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "notification.alerts")
    RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "amq.topic")
    RABBITMQ_ROUTING_KEY = os.getenv("RABBITMQ_ROUTING_KEY", "core.notification.alerts")
    
    # PostgreSQL
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "notify_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "notify_pass")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "notification_db")
    DATABASE_URL = os.getenv("DATABASE_URL", f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    
    # Email
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM = os.getenv("SMTP_FROM")
    
    # SMS
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    
    # Display
    WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")
    
    API_HOST = os.getenv("API_HOST", "localhost")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    
    # Retry
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    RETRY_BACKOFF_BASE = int(os.getenv("RETRY_BACKOFF_BASE", 2))
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
config = Config();