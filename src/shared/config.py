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
    
config = Config();