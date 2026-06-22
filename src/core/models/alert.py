from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class AlertData(BaseModel):
    alertId: str
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    target: str
    # userId: Optional[str] = None
    # userGroupId: Optional[str] = None
    title: str
    message: str

class AlertCreated(BaseModel):
    eventId: str
    eventType: Literal["alert.created"]
    occurredAt: datetime
    correlationId: str
    traceId: str
    source: str
    data: AlertData

class EscalatedData(BaseModel):
    alertId: str
    previousSeverity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    newSeverity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    reason: str
    target: str

class AlertEscalated(BaseModel):
    eventId: str
    eventType: Literal["alert.escalated"]
    occurredAt: datetime
    correlationId: str
    traceId: str
    source: str
    data: EscalatedData

class ResolvedData(BaseModel):
    alertId: str
    resolvedBy: str
    resolutionNote: Optional[str] = None
    target: str

class AlertResolved(BaseModel):
    eventId: str
    eventType: Literal["alert.resolved"]
    occurredAt: datetime
    correlationId: str
    traceId: str
    source: str
    data: ResolvedData