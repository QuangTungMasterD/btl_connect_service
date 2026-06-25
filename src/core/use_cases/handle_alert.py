import asyncio
import logging
from typing import Optional, List
from src.core.models.alert import AlertCreated, AlertEscalated, AlertResolved
from src.core.interfaces import IdempotencyCache, EmailSender, SmsSender, DisplayNotifier
from src.infrastructure.database.repository import NotificationRepository, UserRepository
from src.infrastructure.database.session import AsyncSessionLocal
from src.shared.config import Config

logger = logging.getLogger(__name__)

class HandleAlert:
    def __init__(self, cache: IdempotencyCache, 
                 email: EmailSender, 
                 sms: SmsSender, 
                 display: DisplayNotifier, 
                 telegram,
                 repo: NotificationRepository):
        self.cache = cache
        self.email = email
        self.sms = sms
        self.display = display
        self.telegram = telegram
        self.repo = repo
        self.max_retries = Config.MAX_RETRIES
        self.backoff_base = Config.RETRY_BACKOFF_BASE

    async def _log_channel(self, event_id: str, user_id: str, channel: str, status: str, message: str = None, error: str = None, severity: str = None,):
        try:
            await self.repo.save_log(
                event_id=event_id,
                user_id=user_id,
                channel=channel,
                status=status,
                message=message,
                error_detail=error,
                severity=severity,
            )
        except Exception as e:
            logger.error(f"Failed to save log for {channel}: {e}")

    async def _send_with_retry(self, send_func, recipient: str, subject: Optional[str], message: str, channel_name: str) -> bool:
        """Gửi với retry exponential backoff, trả về True nếu thành công."""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if subject is not None:
                    await send_func(recipient, subject, message)
                else:
                    await send_func(recipient, message)
                    
                logger.info(f"✅ [OUTPUT] {channel_name} sent to {recipient} (attempt {attempt+1})")
                return True
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    delay = self.backoff_base ** attempt
                    logger.warning(f"Retry {attempt+1}/{self.max_retries} for {channel_name} to {recipient} after {delay}s")
                    await asyncio.sleep(delay)
        logger.error(f"All retries failed for {channel_name} to {recipient}: {last_error}")
        return False
    
    async def _log_low_severity(self, event_id: str, user, title: str, message: str, severity: str = "LOW"):
        """Ghi log cho severity LOW (không kênh)"""
        try:
            # Ghi vào bảng notifications với channel = 'log' (cần thêm channel type)
            # Hoặc có thể ghi vào một bảng riêng? Tạm thời dùng channel 'log'
            await self.repo.save_log(
                event_id=event_id,
                user_id=user.id,  # hoặc user.username
                channel="log",    # thêm enum value
                status="success",
                message=f"{title}: {message}",
                error_detail=None,
                severity=severity,
            )
        except Exception as e:
            logger.error(f"Failed to save low severity log: {e}")

    async def _send_to_user(self, event_id: str, user, severity: str, title: str, message: str):
        """Gửi thông báo cho một user qua các kênh phù hợp với severity."""
        full_msg = f"{title}: {message}"
        channels = []
        
        severity = severity.upper()

        if severity in ["CRITICAL", "HIGH"]:
            logger.info("SEVERITY HIGHT or CRITICAL -> send full chanels (email, mock sms, telegram, display)")
            # Gửi tất cả kênh
            if user.email:
                channels.append(("email", self.email.send, f"[ALERT] {title}", user.email))
            if user.phone:
                channels.append(("sms", self.sms.send, None, user.phone))
            if user.telegram_chat_id:  # Nếu user có telegram_chat_id, gửi đến đó, nếu không dùng global
                channels.append(("telegram", self.telegram.send, self.telegram.send, user.telegram_chat_id))
            # Display: dùng username hoặc email làm định danh (có thể là user_id)
            channels.append(("display", self.display.notify, None, user.username))
        elif severity in ["MEDIUM"]:  # LOW / MEDIUM
            logger.info('SEVERITY MEDIUM -> send email & display')
            if user.email:
                channels.append(("email", self.email.send, f"[ALERT] {title}", user.email))
            channels.append(("display", self.display.notify, None, user.username))
        elif severity == "LOW":
            logger.info('SEVERITY LOW -> log only')
            # chỉ log, không gửi kênh nào, nhưng vẫn ghi log channel? Có thể ghi log chung.
            logger.info(f"Low severity alert for user {user.username}, event {event_id}. No notification sent.")
            await self._log_low_severity(event_id, user, title, message, severity=severity)
            return

        if not channels:
            logger.info(f"No channels available for user {user.username}, severity {severity}")
            return

        # Gửi đồng thời các kênh cho user này
        tasks = []
        for channel_name, send_func, subject, recipient in channels:
            task = self._send_with_retry(send_func, recipient, subject, full_msg, channel_name)
            tasks.append((channel_name, recipient, task))

        results = await asyncio.gather(*[task for _, _, task in tasks])
        for (channel_name, recipient, _), success in zip(tasks, results):
            status = "success" if success else "failed"
            await self._log_channel(
                event_id=event_id,
                user_id=recipient,
                channel=channel_name,
                status=status,
                message=full_msg,
                error=None if success else "Failed after retries",
                severity=severity,
            )

    async def process_created(self, event: AlertCreated):
        if await self.cache.is_processed(event.eventId):
            logger.info(f"Duplicate event {event.eventId}, skipping")
            return

        try:
            target = event.data.target
            severity = event.data.severity
            title = event.data.title
            message = event.data.message

            async with AsyncSessionLocal() as session:
                user_repo = UserRepository(session)
                if target == "all":
                    users = await user_repo.get_all_users()
                elif target.startswith("user:"):
                    user_id = target.split(":")[1]
                    user = await user_repo.get_user_by_id(user_id)
                    users = [user] if user else []
                else:
                    users = await user_repo.get_users_by_role(target)

                if not users:
                    logger.warning(f"No users found for target {target}, event {event.eventId} logged but not sent")
                    return

                send_tasks = [self._send_to_user(event.eventId, user, severity, title, message) for user in users]
                await asyncio.gather(*send_tasks)
        except Exception as e:
            logger.error(f"Error processing created event {event.eventId}: {e}")
        finally:
            # Luôn đánh dấu processed sau khi đã cố gắng xử lý (dù thành công hay thất bại)
            await self.cache.mark_processed(event.eventId)

    async def process_escalated(self, event: AlertEscalated):
        if await self.cache.is_processed(event.eventId):
            logger.info(f"Duplicate event {event.eventId}, skipping")
            return

        try:
            target = event.data.target
            severity = event.data.newSeverity
            title = f"Alert {event.data.alertId} escalated"
            message = f"Alert {event.data.alertId} escalated from {event.data.previousSeverity} to {event.data.newSeverity}. Reason: {event.data.reason}"

            async with AsyncSessionLocal() as session:
                user_repo = UserRepository(session)
                if target == "all":
                    users = await user_repo.get_all_users()
                elif target.startswith("user:"):
                    user_id = target.split(":")[1]
                    user = await user_repo.get_user_by_id(user_id)
                    users = [user] if user else []
                else:
                    users = await user_repo.get_users_by_role(target)

                if not users:
                    logger.warning(f"No users found for target {target} in escalated event, logging only")
                    return

                send_tasks = [self._send_to_user(event.eventId, user, severity, title, message) for user in users]
                await asyncio.gather(*send_tasks)
        except Exception as e:
            logger.error(f"Error processing escalated event {event.eventId}: {e}")
        finally:
            await self.cache.mark_processed(event.eventId)

    async def process_resolved(self, event: AlertResolved):
        if await self.cache.is_processed(event.eventId):
            logger.info(f"Duplicate event {event.eventId}, skipping")
            return

        try:
            target = event.data.target
            severity = "LOW"
            title = f"Alert {event.data.alertId} resolved"
            message = f"Alert {event.data.alertId} resolved by {event.data.resolvedBy}. Note: {event.data.resolutionNote or ''}"

            logger.info(f'GET user by target: {target}')
            async with AsyncSessionLocal() as session:
                user_repo = UserRepository(session)
                if target == "all":
                    users = await user_repo.get_all_users()
                elif target.startswith("user:"):
                    user_id = target.split(":")[1]
                    user = await user_repo.get_user_by_id(user_id)
                    users = [user] if user else []
                else:
                    users = await user_repo.get_users_by_role(target)

                if not users:
                    logger.warning(f"No users found for target {target} in resolved event, logging only")
                    return

                send_tasks = [self._send_to_user(event.eventId, user, severity, title, message) for user in users]
                await asyncio.gather(*send_tasks)
        except Exception as e:
            logger.error(f"Error processing resolved event {event.eventId}: {e}")
        finally:
            await self.cache.mark_processed(event.eventId)