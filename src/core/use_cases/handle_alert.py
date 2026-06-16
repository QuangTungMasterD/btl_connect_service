from src.core.models.alert import AlertCreated, AlertEscalated, AlertResolved
from src.core.interfaces import IdempotencyCache, EmailSender, SmsSender, DisplayNotifier
import logging

logger = logging.getLogger(__name__)

class HandleAlert:
    def __init__(self, cache: IdempotencyCache, email: EmailSender, sms: SmsSender, display: DisplayNotifier):
        self.cache = cache
        self.email = email
        self.sms = sms
        self.display = display

    async def process_created(self, event: AlertCreated):
        if await self.cache.is_processed(event.eventId):
            logger.info(f"Duplicate event {event.eventId}, skipping")
            return
        # Xác định người nhận
        user_id = event.data.userId or event.data.userGroupId
        if not user_id:
            logger.error("Missing userId or userGroupId")
            return
        
        severity = event.data.severity
        title = event.data.title
        message = event.data.message
        full_msg = f"{title}: {message}"
        
        if severity in ["CRITICAL", "HIGH"]:
            # Gửi SMS (nếu có cấu hình, nếu không thì mock)
            await self.sms.send(user_id, full_msg)
            # Gửi display notification
            await self.display.notify(user_id, full_msg)
            # Email dự phòng (tùy chọn)
            await self.email.send(user_id, f"[ALERT] {title}", full_msg)
        else:
            # LOW/MEDIUM chỉ gửi email
            await self.email.send(user_id, title, full_msg)
        
        await self.cache.mark_processed(event.eventId)

    async def process_escalated(self, event: AlertEscalated):
        if await self.cache.is_processed(event.eventId):
            logger.info(f"Duplicate event {event.eventId}, skipping")
            return
        user_id = event.data.alertId  # Thực tế cần user_id từ somewhere, ở đây tạm dùng alertId
        msg = f"Alert {event.data.alertId} escalated from {event.data.previousSeverity} to {event.data.newSeverity}. Reason: {event.data.reason}"
        # Escalated nên gửi SMS + display
        await self.sms.send(user_id, msg)
        await self.display.notify(user_id, msg)
        await self.email.send(user_id, "Alert Escalated", msg)
        await self.cache.mark_processed(event.eventId)

    async def process_resolved(self, event: AlertResolved):
        if await self.cache.is_processed(event.eventId):
            logger.info(f"Duplicate event {event.eventId}, skipping")
            return
        user_id = event.data.resolvedBy
        msg = f"Alert {event.data.alertId} resolved by {event.data.resolvedBy}. Note: {event.data.resolutionNote or ''}"
        await self.email.send(user_id, "Alert Resolved", msg)
        await self.display.notify(user_id, msg)
        await self.cache.mark_processed(event.eventId)