from src.core.interfaces import SmsSender
import logging

logger = logging.getLogger(__name__)

class MockSmsSender(SmsSender):
    async def send(self, to: str, subject: str = None, message: str = None):
        logger.info(f"[MOCK SMS] To: {to}, Message: {message}")