from pydantic import BaseModel, Field
from typing import Optional


class Message(BaseModel):
    message: str


class HistoryItem(BaseModel):
    role: str
    message: str
    emotion: Optional[str] = None
    intern: Optional[str] = None 


class User(BaseModel):
    id: int = Field(..., title="User ID", description="Unique identifier for the user")


class Response(BaseModel):
    user_id: int
    message: str