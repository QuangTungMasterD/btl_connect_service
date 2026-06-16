import json
import aio_pika
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
            RuntimeState.update(
                rabbit_connected=True
            )
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            queue = await self.channel.declare_queue(Config.RABBITMQ_QUEUE, durable=True)
            await queue.bind(Config.RABBITMQ_EXCHANGE, Config.RABBITMQ_ROUTING_KEY)
            return queue
        except Exception:
            RuntimeState.update(
                rabbit_connected=False
            )
            raise
    
    async def consume(self, callback):
        queue = await self.connect()
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = json.loads(message.body.decode())
                    await callback(body)