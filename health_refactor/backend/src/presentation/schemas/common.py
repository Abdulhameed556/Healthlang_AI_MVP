"""Shared payload models referenced in OpenAPI (health, etc.)."""
from pydantic import BaseModel, Field


class HealthData(BaseModel):
    status: str = Field(..., description="Service health indicator", examples=["ok"])
