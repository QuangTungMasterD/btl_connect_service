import asyncio
import logging
from typing import Optional, List
from datetime import datetime
from src.core.models.alert import AlertCreated, AlertEscalated, AlertResolved
from src.core.interfaces import IdempotencyCache, EmailSender, SmsSender, DisplayNotifier
from src.infrastructure.database.repository import NotificationRepository, UserRepository
from src.infrastructure.database.session import AsyncSessionLocal
from src.shared.config import Config
# template
from src.core.templates.email_template import build_email_content
from src.core.templates.telegram_template import build_telegram_content

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

    async def _log_channel(self, event_id: str, user_id: str, channel: str, status: str, message: str = None, error: str = None, severity: str = None,
                   retry_count: int = 0):
        try:
            async with AsyncSessionLocal() as session:
                self.repo = NotificationRepository(session)
                await self.repo.save_log(
                    event_id=event_id,
                    user_id=user_id,
                    channel=channel,
                    status=status,
                    message=message,
                    error_detail=error,
                    severity=severity,
                    retry_count=retry_count,
                )
        except Exception as e:
            logger.error(f"Failed to save log for {channel}: {e}")

    async def _send_with_retry(self, send_func, recipient: str, subject: Optional[str],
                               message: str, channel_name: str, is_html: bool = False) -> tuple[bool, int]:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                if channel_name == "email":
                    if is_html:
                        await send_func(recipient, subject, message, html=True)
                    else:
                        await send_func(recipient, subject, message)
                else:
                    # Telegram đã tự xử lý parse_mode bên trong sender
                    await send_func(recipient, subject, message)
                logger.info(f"✅ [OUTPUT] {channel_name} sent to {recipient}")
                return True, attempt
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries - 1:
                    delay = self.backoff_base ** attempt
                    logger.warning(f"Retry {attempt+1} for {channel_name}")
                    await asyncio.sleep(delay)
        logger.error(f"All retries failed for {channel_name}: {last_error}")
        return False, self.max_retries - 1

    async def _log_low_severity(self, event_id: str, user, title: str, message: str, severity: str = "LOW"):
        try:
            await self.repo.save_log(
                event_id=event_id,
                user_id=user.id,
                channel="log",
                status="success",
                message=f"{title}: {message}",
                error_detail=None,
                severity=severity,
            )
        except Exception as e:
            logger.error(f"Failed to save low severity log: {e}")

    async def _send_to_user(self, event_id: str, user, severity: str, title: str, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        full_msg = f"""🚨SYSTEM ALERT -🔸{severity}🔸\n[Event id]: {event_id}\n[Target user]: {user.id}\n[Title]: {title}\n[Time]: {timestamp}\n[Message]: {message} """
        channels = []
        severity = severity.upper()

        if severity in ["CRITICAL", "HIGH"]:
            logger.info("SEVERITY HIGH or CRITICAL -> send full channels")
            # EMAIL - dùng template
            if user.email:
                subject, html_content = build_email_content(
                    event_id=event_id,
                    user_id=str(user.id),
                    username=user.username,
                    user_role=user.role,
                    severity=severity,
                    title=title,
                    message=message,
                    timestamp=timestamp
                )
                channels.append({
                    "channel": "email",
                    "send_func": self.email.send,
                    "subject": subject,
                    "recipient": user.email,
                    "message": html_content,
                    "is_html": True
                })
            # SMS - dùng full_msg
            if user.phone:
                channels.append({
                    "channel": "sms",
                    "send_func": self.sms.send,
                    "subject": None,
                    "recipient": user.phone,
                    "message": full_msg,
                    "is_html": False
                })
            # TELEGRAM - dùng template
            if user.telegram_chat_id:
                tg_text = build_telegram_content(
                    event_id=event_id,
                    user_id=str(user.id),
                    username=user.username,
                    user_role=user.role,
                    severity=severity,
                    title=title,
                    message=message,
                    timestamp=timestamp
                )
                channels.append({
                    "channel": "telegram",
                    "send_func": self.telegram.send,
                    "subject": None,
                    "recipient": user.telegram_chat_id,
                    "message": tg_text,
                    "is_html": False
                })
            # DISPLAY - dùng full_msg
            channels.append({
                "channel": "display",
                "send_func": self.display.notify,
                "subject": None,
                "recipient": user.username,
                "message": full_msg,
                "is_html": False
            })

        elif severity == "MEDIUM":
            logger.info('SEVERITY MEDIUM -> send email & display')
            if user.email:
                subject, html_content = build_email_content(
                    event_id=event_id,
                    user_id=str(user.id),
                    username=user.username,
                    user_role=user.role,
                    severity=severity,
                    title=title,
                    message=message,
                    timestamp=timestamp
                )
                channels.append({
                    "channel": "email",
                    "send_func": self.email.send,
                    "subject": subject,
                    "recipient": user.email,
                    "message": html_content,
                    "is_html": True
                })
            channels.append({
                "channel": "display",
                "send_func": self.display.notify,
                "subject": None,
                "recipient": user.username,
                "message": full_msg,
                "is_html": False
            })

        elif severity == "LOW":
            logger.info('SEVERITY LOW -> log only')
            await self._log_low_severity(event_id, user, title, message, severity=severity)
            return

        if not channels:
            logger.info(f"No channels available for user {user.username}, severity {severity}")
            return

        tasks = []
        for ch in channels:
            task = self._send_with_retry(
                ch["send_func"],
                ch["recipient"],
                ch["subject"],
                ch["message"],
                ch["channel"],
                ch["is_html"]
            )
            tasks.append((ch["channel"], ch["recipient"], ch["message"], task))

        results = await asyncio.gather(*[t for _, _, _, t in tasks])
        for (channel_name, recipient, msg, _), (success, retry_count) in zip(tasks, results):
            status = "success" if success else "failed"
            await self._log_channel(
                event_id=event_id,
                user_id=recipient,
                channel=channel_name,
                status=status,
                message=msg,
                error=None if success else "Failed after retries",
                severity=severity,
                retry_count=retry_count,
            )

    # Các method process_created, process_escalated, process_resolved giữ nguyên (không thay đổi)
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