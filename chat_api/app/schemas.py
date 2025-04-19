from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SessionCreate(BaseModel):
    client_id: Optional[str] = None

class MessageRequest(BaseModel):
    content: str

class AgentRecommendation(BaseModel):
    intent: str
    emotion: str
    actions: list[str]
    knowledge: str

class SessionComplete(BaseModel):
    operator_notes: str