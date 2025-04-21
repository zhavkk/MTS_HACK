from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class SessionCreate(BaseModel):
    pass

class MessageRequest(BaseModel):
    content: str
    role: str = "operator"  # Default to operator role

class Recommendation(BaseModel):
    link: str
    intern: str
    know: str
    emotinal: str
    ans: str

class SessionComplete(BaseModel):
    pass

class AgentResponse(BaseModel):
    recommendations: List[Recommendation]
    error: Optional[str] = None

class CallbackRequest(BaseModel):
    recommendation: Recommendation

class SessionResponse(BaseModel):
    session_id: str

class SessionData(BaseModel):
    messages: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    last_update: datetime
    client_id: str