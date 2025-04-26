from pydantic import BaseModel, Field
from typing import Optional, List


class UserId(BaseModel):
    user_id: int = Field(..., description="ID of the user")


class Knowledge(BaseModel):
    answer: str
    source: Optional[str] = None


class Answer(BaseModel):
    answer: str


class Response(BaseModel):
    id: int
    answer: str


class HistoryItem(BaseModel):
    role: str
    message: str
    emotion: Optional[str] = None
    intern: Optional[str] = None     


class SuggestionRequest(BaseModel):
    emotion: str
    intent: str
    rag: dict
    client_message: str
