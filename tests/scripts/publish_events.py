#!/usr/bin/env python3
"""
publish_events.py - Gửi 3 event mẫu vào RabbitMQ cho B7 test
Usage: python publish_events.py [--host localhost] [--port 5672]
"""

import asyncio
import aio_pika
import json
import uuid
import argparse
from datetime import datetime

async def publish_event(host, port, event_type, data_override=None):
    """Gửi một event với event_type và data_override (dict)"""
    connection = await aio_pika.connect_robust(f"amqp://guest:guest@{host}:{port}/")
    async with connection:
        channel = await connection.channel()
        event_id = str(uuid.uuid4())
        base_event = {
            "eventId": event_id,
            "eventType": event_type,
            "occurredAt": datetime.now().isoformat(),
            "correlationId": "corr-" + str(uuid.uuid4())[:8],
            "traceId": "trace-" + str(uuid.uuid4())[:8],
            "source": "test-script",
            "data": {}
        }

        # Default data theo từng loại
        if event_type == "alert.created":
            base_event["data"] = {
                "alertId": "test-001",
                "severity": "HIGH",
                "target": "security_team",
                "title": "Test Alert Created",
                "message": "This is a test alert"
            }
        elif event_type == "alert.escalated":
            base_event["data"] = {
                "alertId": "test-001",
                "previousSeverity": "MEDIUM",
                "newSeverity": "CRITICAL",
                "reason": "Escalation due to repeated violations",
                "target": "admin"
            }
        elif event_type == "alert.resolved":
            base_event["data"] = {
                "alertId": "test-001",
                "resolvedBy": "admin",
                "resolutionNote": "Issue fixed",
                "target": "staff"
            }
        else:
            raise ValueError(f"Unsupported event_type: {event_type}")

        # Merge override nếu có
        if data_override:
            base_event["data"].update(data_override)

        exchange = await channel.get_exchange("amq.topic")
        await exchange.publish(
            aio_pika.Message(body=json.dumps(base_event).encode()),
            routing_key="notification.alerts"
        )
        return event_id

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost", help="RabbitMQ host")
    parser.add_argument("--port", type=int, default=5672, help="RabbitMQ port")
    args = parser.parse_args()

    # Gửi 3 event và in event IDs
    print("📤 Publishing test events...")
    created_id = await publish_event(args.host, args.port, "alert.created")
    print(f"   Created: {created_id}")
    await asyncio.sleep(0.5)  # chờ nhẹ để không bị trùng
    escalated_id = await publish_event(args.host, args.port, "alert.escalated")
    print(f"   Escalated: {escalated_id}")
    await asyncio.sleep(0.5)
    resolved_id = await publish_event(args.host, args.port, "alert.resolved")
    print(f"   Resolved: {resolved_id}")

    # Trả về event ID của created để dùng làm filter
    print(created_id)  # dòng cuối để script bash lấy được

if __name__ == "__main__":
    asyncio.run(main())