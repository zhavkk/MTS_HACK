from pydantic import BaseModel

class MessageRequest(BaseModel):
    """Request model for adding a message to a session."""
    content: str
    role: str = "operator"  # Default to operator role

class SessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str 