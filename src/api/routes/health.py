from fastapi import APIRouter
from datetime import datetime
from src.shared.config import Config
from src.shared.runtime_state import RuntimeState

router = APIRouter()

@router.get("/health")
async def health():

    state = RuntimeState.load()

    return {
        "status": "ok" if state["rabbit_connected"] else "degraded",
        "service": Config.SERVICE_NAME,
        "version": Config.SERVICE_VERSION,
        "rabbitmq": state["rabbit_connected"],
        "processedEvents": state["processed_events"],
        "lastEventAt": state["last_event_at"]
    }
