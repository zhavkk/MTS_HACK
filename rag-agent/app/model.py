from pydantic import BaseModel, Field
from typing import Optional


class HistoryItem(BaseModel):
    role: str
    message: str
    emotion: Optional[str] = None
    intern: Optional[str] = None 


class Knowledge(BaseModel):
    answer: str
    source: str


class Response(BaseModel):
    user_id: int
    message: Knowledge


class SearchResult(BaseModel):
    answer: str
    source: str
    

class UserId(BaseModel):
    user_id: int = Field(..., description="ID of the user")