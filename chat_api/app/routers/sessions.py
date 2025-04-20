from fastapi import APIRouter, HTTPException
from ..models import MessageRequest, SessionResponse
from ..schemas import SessionCreate, SessionData, CallbackRequest
from ..services.message_buffer import MessageBuffer

router = APIRouter()
message_buffer = MessageBuffer()

@router.post("/sessions", response_model=SessionResponse)
async def create_session():
    """Create a new session."""
    try:
        session_id = message_buffer.create_session()
        return SessionResponse(session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions/{session_id}/messages")
async def add_message(session_id: str, message: MessageRequest):
    """Add a message to the session."""
    try:
        await message_buffer.add_message(session_id, message.content, message.role)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session data including messages and recommendations."""
    if not message_buffer.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return message_buffer.get_session_data(session_id)

@router.post("/sessions/{session_id}/complete")
async def complete_session(session_id: str):
    """Complete the session."""
    try:
        result = await message_buffer.complete_session(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/callback")
async def handle_callback(callback: CallbackRequest):
    """Handle recommendation service callback."""
    try:
        message_buffer.add_recommendation(callback.session_id, callback.recommendation.dict())
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/updates", response_model=SessionData)
async def get_updates(session_id: str):
    """Get session updates including messages and recommendations."""
    try:
        if not message_buffer.session_exists(session_id):
            raise HTTPException(status_code=404, detail="Session not found")
        return message_buffer.get_session_data(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))