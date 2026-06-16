from src.core.interfaces import SmsSender
import logging

logger = logging.getLogger(__name__)

class MockSmsSender(SmsSender):
    async def send(self, to: str, message: str):
        logger.info(f"[MOCK SMS] To: {to}, Message: {message}")