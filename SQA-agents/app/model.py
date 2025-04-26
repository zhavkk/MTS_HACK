from pydantic import BaseModel
from typing import List, Dict


class Message(BaseModel):
    role: str
    content: str


class DialogueRequest(BaseModel):
    user_id: int


class SummaryQAACombinedResponse(BaseModel):
    summary: Dict
    quality_review: Dict
