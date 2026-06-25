import asyncio
import logging
import json
from datetime import datetime
from src.core.models.alert import AlertCreated, AlertEscalated, AlertResolved
from src.core.use_cases.handle_alert import HandleAlert
from src.infrastructure.rabbitmq.consumer import RabbitMQConsumer
from src.infrastructure.email.smtp_sender import SmtpEmailSender
from src.infrastructure.sms.mock_sms import MockSmsSender
from src.infrastructure.display.sse_notifier import SseDisplayNotifier
from src.infrastructure.telegram.telegram_sender import TelegramSender
from src.infrastructure.cache.memory_cache import MemoryCache
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.repository import NotificationRepository
from src.shared.runtime_state import RuntimeState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cache = MemoryCache()

async def callback(body):
    event_type = body.get("eventType")
    event_id = body.get("eventId")
    
    logger.info(f"📥 [INPUT] Event received: {event_type} | ID: {event_id}")
    logger.info(f"📥 [INPUT] Full payload: {json.dumps(body, indent=2)}")
    
    # Tạo session và repository mới cho mỗi event
    async with AsyncSessionLocal() as session:
        repo = NotificationRepository(session)
        email = SmtpEmailSender()
        sms = MockSmsSender()
        telegram = TelegramSender()
        display = SseDisplayNotifier()
        handler = HandleAlert(cache, email, sms, display, telegram, repo)

        data = RuntimeState.load()
        try:
            if event_type == "alert.created":
                event = AlertCreated(**body)
                await handler.process_created(event)
            elif event_type == "alert.escalated":
                event = AlertEscalated(**body)
                await handler.process_escalated(event)
            elif event_type == "alert.resolved":
                event = AlertResolved(**body)
                await handler.process_resolved(event)
            else:
                logger.warning(f"Unknown event type: {event_type}")

            RuntimeState.update(
                processed_events=data["processed_events"] + 1,
                last_event_at=datetime.utcnow().isoformat()
            )
            
            logger.info(f"✅ [OUTPUT] Event {event_id} processed successfully")
        except Exception as e:
            RuntimeState.update(
                failed_events=data["failed_events"] + 1
            )
            logger.error(f"Error processing event: {e}")

async def main():
    RuntimeState.update(
        rabbit_connected=False,
        processed_events=0,
        failed_events=0,
        last_event_at=None
    )
    logger.info("Starting consumer...")
    consumer = RabbitMQConsumer()
    await consumer.consume(callback)

if __name__ == "__main__":
    asyncio.run(main())