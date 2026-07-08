from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from typing import Optional
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.database.repository import NotificationRepository

router = APIRouter()

@router.get("/logs")
async def get_logs_api(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_id: Optional[str] = None,
    user_id: Optional[str] = None,
    channel: Optional[str] = None,
    status: Optional[str] = None,
):
    async with AsyncSessionLocal() as session:
        repo = NotificationRepository(session)
        logs = await repo.get_logs(
            limit=limit,
            offset=offset,
            event_id=event_id,
            user_id=user_id,
            channel=channel,
            status=status,
        )
        result = [
            {
                "id": str(log.id),
                "event_id": log.event_id,
                "user_id": log.user_id,
                "channel": log.channel,
                "status": log.status,
                "message": log.message,
                "error_detail": log.error_detail,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "sent_at": log.sent_at.isoformat() if log.sent_at else None,
                "severity": log.severity,
                "retry_count": log.retry_count,
            }
            for log in logs
        ]
        return {
            "data": result,
            "total": len(result),
            "limit": limit,
            "offset": offset,
        }
