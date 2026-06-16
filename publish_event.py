import asyncio
import aio_pika
import json
from datetime import datetime

async def publish():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost:5672/")
    async with connection:
        channel = await connection.channel()
        event = {
            "eventId": "test-001",
            "eventType": "alert.created",
            "occurredAt": datetime.now().isoformat(),
            "correlationId": "corr-123",
            "traceId": "trace-456",
            "source": "core-business",
            "data": {
                "alertId": "alert-999",
                "severity": "CRITICAL",
                "userId": "user-123",
                "title": "🔥 Test Critical Alert",
                "message": "This is a test message from publish script"
            }
        }
        routing_key = "core.notification.alerts"
        # Lấy exchange amq.topic (topic exchange)
        exchange = await channel.get_exchange("amq.topic")
        await exchange.publish(
            aio_pika.Message(body=json.dumps(event).encode()),
            routing_key=routing_key
        )
        print(f"✅ Event published to {routing_key} via amq.topic")

if __name__ == "__main__":
    asyncio.run(publish())