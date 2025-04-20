from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class SessionCreate(BaseModel):
    """Model for session creation."""
    pass

class MessageRequest(BaseModel):
    """Request model for adding a message to a session."""
    content: str
    role: str  # "user" или "operator"

class AgentRecommendation(BaseModel):
    """Model for recommendation from agent service."""
    intent: str
    emotion: str
    actions: List[str]
    knowledge: str

class SessionComplete(BaseModel):
    """Model for session completion."""
    pass

class AgentResponse(BaseModel):
    recommendations: List[AgentRecommendation]
    error: Optional[str] = None

class CallbackRequest(BaseModel):
    """Model for recommendation service callback."""
    session_id: str
    recommendation: AgentRecommendation

class SessionData(BaseModel):
    """Model for session data response."""
    messages: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    last_update: datetime
    client_id: str