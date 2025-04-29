from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class Message(BaseModel):
    user_id: str = Field(..., description="ID of the user who sent the message")
    text: str = Field(..., description="Content of the message")

class Answer(BaseModel):
    answer: str
    
class SummaryQAACombinedResponse(BaseModel):
    summary: Dict
    quality_review: Dict
    
class ListAnswer(BaseModel):
    answers: List[Answer] = Field(..., description="List of answers")

class UserId(BaseModel):
    user_id: int = Field(..., description="ID of the user")

class LastMessage(BaseModel):
    content: Message = Field(..., description="The last message sent in the chat")

class Knowledge(BaseModel):
    answer: str
    source: Optional[str] = None

class HistoryItem(BaseModel):
    role: str
    message: str
    emotion: Optional[str] = None
    intern: Optional[str] = None 

class KnowledgeHistoryItem(BaseModel):
    knowledge: List[Knowledge] = Field(..., description="List of knowledge items")

class HistoryResponse(BaseModel):
    response: List[HistoryItem]

class Response(BaseModel):
    response: str = Field(..., description="Response to the last message")

class BulkHistory(BaseModel):
    user_id: int = Field(..., description="ID пользователя, для которого история")
    response: List[HistoryItem] = Field(
        ..., description="Список элементов истории"
    )


class BulkResponse(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    ans: str
    history:   HistoryItem = Field(..., description="Последние пользовательские сообщения")
    knowledge: Knowledge  = Field(..., description="Последние данные из базы знаний")
    
class AllDialogues(BaseModel):
    user_id: str = Field(..., description="ID of the user")
    text: List[Message] = Field(..., description="List of all messages in the chat")