from sqlalchemy.ext.asyncio import AsyncSession
from src.infrastructure.database.models import NotificationLog, User
from sqlalchemy import select, desc
from datetime import datetime
from typing import List, Optional

class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_log(self, event_id: str, user_id: str, channel: str, status: str, message: str = None, error_detail: str = None, severity: str = None,):
        log = NotificationLog(
            event_id=event_id,
            user_id=user_id,
            channel=channel,
            status=status,
            message=message,
            error_detail=error_detail,
            severity=severity,
            sent_at=datetime.utcnow()
        )
        self.session.add(log)
        await self.session.commit()
        return log
    
    async def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        event_id: Optional[str] = None,
        user_id: Optional[str] = None,
        channel: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[NotificationLog]:
        """Lấy danh sách log với phân trang và lọc."""
        query = select(NotificationLog).order_by(desc(NotificationLog.created_at))
        
        if event_id:
            query = query.where(NotificationLog.event_id == event_id)
        if user_id:
            query = query.where(NotificationLog.user_id == user_id)
        if channel:
            query = query.where(NotificationLog.channel == channel)
        if status:
            query = query.where(NotificationLog.status == status)
        
        query = query.offset(offset).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_users_by_role(self, role: str) -> List[User]:
        result = await self.session.execute(select(User).where(User.role == role))
        return result.scalars().all()

    async def get_all_users(self) -> List[User]:
        result = await self.session.execute(select(User))
        return result.scalars().all()
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()