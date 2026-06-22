import json
import aio_pika
from aio_pika import ExchangeType
from src.core.interfaces import MessageBroker
from src.shared.config import Config
from src.shared.runtime_state import RuntimeState
import logging

logger = logging.getLogger(__name__)

class RabbitMQConsumer(MessageBroker):
    def __init__(self):
        self.connection = None
        self.channel = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(
                f"amqp://{Config.RABBITMQ_USER}:{Config.RABBITMQ_PASS}@{Config.RABBITMQ_HOST}:{Config.RABBITMQ_PORT}/"
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)

            # === FIX CHÍNH ===
            exchange = await self.channel.declare_exchange(
                Config.RABBITMQ_EXCHANGE,
                ExchangeType.TOPIC,
                durable=True
            )

            queue = await self.channel.declare_queue(
                Config.RABBITMQ_QUEUE,
                durable=True
            )

            await queue.bind(exchange, Config.RABBITMQ_ROUTING_KEY)

            RuntimeState.update(rabbit_connected=True)
            logger.info("✅ CONSUMER CONNECTED SUCCESSFULLY")
            logger.info(f"Queue: {Config.RABBITMQ_QUEUE} | Exchange: {Config.RABBITMQ_EXCHANGE} | Key: {Config.RABBITMQ_ROUTING_KEY}")
            return queue

        except Exception as e:
            RuntimeState.update(rabbit_connected=False)
            logger.error(f"❌ RabbitMQ connect failed: {e}")
            raise

    async def consume(self, callback):
        queue = await self.connect()
        logger.info("🚀 Consumer is listening...")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                        logger.info(f"📥 RECEIVED: {body.get('eventType')} | {body.get('eventId')}")
                        await callback(body)
                    except Exception as e:
                        logger.error(f"❌ Error processing: {e}")