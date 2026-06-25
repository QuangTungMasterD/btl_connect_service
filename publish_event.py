import asyncio
import aio_pika
import json
from datetime import datetime
import uuid

# ===== CẤU HÌNH TEST - SỬA Ở ĐÂY =====
TARGET = "security_team"      # "security_team", "admin", "staff", "all"
SEVERITY = "HIGH"             # "LOW", "MEDIUM", "HIGH", "CRITICAL"
EVENT_TYPE = "alert.created"  # "alert.created", "alert.escalated", "alert.resolved"
ALERT_ID = "alert-test-001"
TITLE = "Quang Tùng MasterD"
MESSAGE = "Quang Tùng MasterD"
# =====================================

async def publish():
    # Kết nối RabbitMQ (nếu chạy trong Docker thì dùng host "rabbitmq")
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")
    async with connection:
        channel = await connection.channel()
        event_id = str(uuid.uuid4())

        # Xây dựng event theo đúng schema
        event = {
            "eventId": event_id,
            "eventType": EVENT_TYPE,
            "occurredAt": datetime.now().isoformat(),
            "correlationId": "corr-" + str(uuid.uuid4())[:8],
            "traceId": "trace-" + str(uuid.uuid4())[:8],
            "source": "core-business",
            "data": {
                "alertId": ALERT_ID,
                "severity": SEVERITY,
                "target": TARGET,
                "title": TITLE,
                "message": MESSAGE
            }
        }

        # Điều chỉnh data cho các event type đặc biệt
        if EVENT_TYPE == "alert.escalated":
            event["data"].update({
                "previousSeverity": "LOW",
                "newSeverity": SEVERITY,
                "reason": "Cảnh báo leo thang do lặp lại nhiều lần",
                "target": TARGET
            })
        elif EVENT_TYPE == "alert.resolved":
            event["data"].update({
                "resolvedBy": "admin",
                "resolutionNote": "Đã xử lý xong sự cố",
                "target": TARGET
            })

        # Gửi lên exchange với routing key
        routing_key = "notification.alerts"
        exchange = await channel.get_exchange("amq.topic")
        await exchange.publish(
            aio_pika.Message(body=json.dumps(event).encode()),
            routing_key=routing_key
        )

        print(f"✅ Đã gửi event:")
        print(f"   Event ID  : {event_id}")
        print(f"   Type      : {EVENT_TYPE}")
        print(f"   Target    : {TARGET}")
        print(f"   Severity  : {SEVERITY}")
        print(f"   Routing   : {routing_key}")

if __name__ == "__main__":
    asyncio.run(publish())