import asyncio
import json
from src.core.models.alert import AlertCreated, AlertEscalated, AlertResolved
from src.core.use_cases.handle_alert import HandleAlert
from src.infrastructure.rabbitmq.consumer import RabbitMQConsumer
from src.infrastructure.email.smtp_sender import SmtpEmailSender
from src.infrastructure.sms.mock_sms import MockSmsSender
from src.infrastructure.display.sse_notifier import SseDisplayNotifier
from src.infrastructure.cache.memory_cache import MemoryCache
from src.shared.runtime_state import RuntimeState
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
cache = MemoryCache()

async def callback(body):
    event_type = body.get("eventType")
    email = SmtpEmailSender()
    sms = MockSmsSender()
    display = SseDisplayNotifier()
    handler = HandleAlert(cache, email, sms, display)
    
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
    except Exception as e:
        data = RuntimeState.load()
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
    logger.info("ok....")
    await consumer.consume(callback)

if __name__ == "__main__":
    asyncio.run(main())