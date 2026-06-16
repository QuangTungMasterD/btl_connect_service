from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import verify_token
from src.shared.runtime_state import RuntimeState

router = APIRouter()

@router.get("/metrics/queue")
async def queue_metrics(
    _ = Depends(verify_token)
):
    state = RuntimeState.load()

    return {
        "queueName": "notification.alerts",
        "processedEvents": state["processed_events"],
        "failedEvents": state["failed_events"],
        "lastEventAt": state["last_event_at"],
        "consumerAlive": state["rabbit_connected"]
    }