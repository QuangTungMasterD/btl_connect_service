import logging
import httpx
from src.core.interfaces import ChannelSender
from src.shared.config import Config

logger = logging.getLogger(__name__)

class TelegramSender(ChannelSender):
    async def send(self, recipient: str, subject: str, message: str) -> None:
        """Gửi tin nhắn Telegram qua Bot API.
           recipient: chat_id (có thể là group/channel/user id)
           subject: không sử dụng, chỉ để giữ đồng bộ với interface
        """
        token = Config.TELEGRAM_BOT_TOKEN
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not configured")
            return
        chat_id = recipient or Config.TELEGRAM_CHAT_ID
        if not chat_id:
            logger.error("No chat_id provided and TELEGRAM_CHAT_ID not configured")
            return
        
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"{message}",
            "parse_mode": "HTML"
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10.0)
                resp.raise_for_status()
            logger.info(f"Telegram message sent to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send Telegram: {e}")
            raise