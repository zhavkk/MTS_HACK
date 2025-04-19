from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..schemas import SessionComplete,SessionCreate,MessageRequest
from ..services.message_buffer import MessageBuffer
from ..services.agent_client import AgentClient

router = APIRouter(prefix="/sessions", tags=["sessions"])

buffer_service = MessageBuffer()
agent_client = AgentClient()

@router.post("", response_model=dict)
async def create_session():
    session_id = buffer_service.create_session()
    return {"session_id": session_id}

@router.post("/{session_id}/messages")
async def add_message(
    session_id: str,
    message: MessageRequest,
    bg_tasks: BackgroundTasks
):
    if not buffer_service.session_exists(session_id):
        raise HTTPException(404, "Session not found")
    
    bg_tasks.add_task(
        buffer_service.add_message,
        session_id,
        message.content
    )
    
    return {"status": "processing"}

@router.post("/{session_id}/complete")
async def complete_session(
    session_id: str,
    data: SessionComplete
):
    if not buffer_service.session_exists(session_id):
        raise HTTPException(404, "Session not found")
    
    dialog_data = buffer_service.get_session_data(session_id)
    dialog_data["operator_notes"] = data.operator_notes
    
    # Отправка в CRM
    await agent_client.send_to_crm(dialog_data)
    
    # Очистка буфера
    buffer_service.delete_session(session_id)
    
    return {"status": "completed"}