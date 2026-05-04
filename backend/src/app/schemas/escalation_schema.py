from pydantic import BaseModel, Field
from typing import Optional


class EscalationResolveSchema(BaseModel):
    status: str = Field(description="resolved or dismissed")
    resolution_notes: Optional[str] = None
