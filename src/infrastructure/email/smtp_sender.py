import smtplib
from email.message import EmailMessage
from src.core.interfaces import EmailSender
from src.shared.config import Config
import logging

logger = logging.getLogger(__name__)

class SmtpEmailSender(EmailSender):
    async def send(self, to: str, subject: str, body: str):
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = Config.SMTP_FROM
        msg["To"] = to
        
        try:
            with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as smtp:
                smtp.starttls()
                smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                smtp.send_message(msg)
            logger.info(f"Email sent to {to}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")