"""Pydantic request/response schemas for internal."""
from pydantic import BaseModel, Field


class TriggerTestTaskRequest(BaseModel):
    message: str = Field(default="ping", max_length=500, description="Echoed back by the worker.")


class TriggerTestTaskResponse(BaseModel):
    enqueued: bool
    task: str
    message: str
    enqueued_at_iso: str
