from fastapi import APIRouter
from src.shared.config import Config

router = APIRouter()

@router.get("/info")
async def info():
    return {
        "name": "notification-service",
        "version": Config.SERVICE_VERSION,
        "pair": "Pair 04 - Core Business → Notification",
        "role": "Provider",
        "mechanism": "queue-async",
        "topic": "core.notification.alerts",
        "events": ["alert.created", "alert.escalated", "alert.resolved"],
        "contractRef": "negotiation-log.md, event-contract-template.md"
    }