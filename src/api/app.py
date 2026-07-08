import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from src.infrastructure.display.sse_notifier import manager, ConnectionManager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Notification Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # cho phép tất cả origin, chỉ dùng cho dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from src.api.routes import health, info, metrics, logs
app.include_router(health.router, tags=["Health"])
app.include_router(info.router, tags=["Info"])
app.include_router(logs.router, tags=["Logs"])
app.include_router(metrics.router, tags=["Metrics"])

# SSE endpoint - dùng StreamingResponse
@app.get("/notifications/stream")
async def stream_notifications():
    async def event_generator():
        queue = await manager.connect()
        try:
            while True:
                message = await queue.get()   # nhận dict
                # Định dạng chuẩn SSE: event: notification\ndata: {...}\n\n
                yield f"event: notification\ndata: {json.dumps(message)}\n\n"
        except asyncio.CancelledError:
            manager.disconnect(queue)
            raise
    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Internal endpoint
@app.post("/internal/notify")
async def internal_notify(request: Request):
    data = await request.json()
    user_id = data.get("userId")
    message = data.get("message")
    timestamp = data.get("timestamp", asyncio.get_event_loop().time())
    await manager.broadcast({
        "userId": user_id,
        "message": message,
        "timestamp": timestamp
    })
    return {"status": "ok"}

# Mount static
app.mount("/", StaticFiles(directory="static", html=True), name="static")
