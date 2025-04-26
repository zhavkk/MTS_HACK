import asyncio
from datetime import datetime
from collections import defaultdict
import uuid
import random
from .agent_client import AgentClient

class MessageBuffer:
    def __init__(self):
        self.sessions = defaultdict(lambda: {
            "messages": [],
            "recommendations": [],
            "last_update": datetime.now(),
            "client_id": None,
            "buffer_timer": None
        })
        self.BUFFER_TIMEOUT = 0
        self.agent_client = AgentClient()

    def session_exists(self, session_id: str) -> bool:
        """Check if session exists."""
        return session_id in self.sessions

    def create_session(self) -> str:
        """Create a new session with a random client ID."""
        session_id = str(uuid.uuid4())
        client_id = str(random.randint(0, 2000))
        
        self.sessions[session_id] = {
            "messages": [],
            "recommendations": [],
            "last_update": datetime.now(),
            "client_id": client_id,
            "buffer_timer": None
        }
        return session_id

    async def add_message(self, session_id: str, content: str, role: str = "operator") -> None:
        """Add a message to the session buffer and process it."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        print(f"Adding message to session {session_id}: {content}")
            
        session = self.sessions[session_id]
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        session["messages"].append(message)
        print(f"Message added to session {session_id}: {message}")
        
        if role == "user":
            if session["client_id"] is None:
                raise ValueError("Client ID is required for user messages")
            print(f"Client ID for session {session_id}: {session['client_id']}")
            
            if not session["buffer_timer"]:
                session["buffer_timer"] = asyncio.create_task(
                    self._process_user_message(session_id, content)
                )
        else:  
            print(f"Sending operator message to recommendation service: {content}")
            await self._process_operator_message(session_id, content)

    async def _process_user_message(self, session_id: str, content: str):
        """Process user message after buffer timeout."""
        try:
            await asyncio.sleep(self.BUFFER_TIMEOUT)
            session = self.sessions[session_id]
            user_messages = [
                msg["content"] for msg in session["messages"] if msg["role"] =="user"
            ]
            full_text = user_messages[-1] if user_messages else ""
            await self.agent_client.send_user_message(session["client_id"], full_text)
        finally:
            session["buffer_timer"] = None
    async def _process_operator_message(self, session_id: str, content: str):
        """Process user message after buffer timeout."""
        try:
            await asyncio.sleep(self.BUFFER_TIMEOUT)
            session = self.sessions[session_id]
            user_messages = [
                msg["content"] for msg in session["messages"] if msg["role"] =="operator"
            ]
            full_text = user_messages[-1] if user_messages else ""
            await self.agent_client.send_operator_message(session["client_id"], full_text)
        finally:
            session["buffer_timer"] = None

    def get_session_data(self, session_id: str):
        """Get session data including messages and recommendations."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
            
        session = self.sessions[session_id]
        return {
            "messages": session["messages"],
            "recommendations": session["recommendations"],
            "last_update": session["last_update"],
            "client_id": session["client_id"]
        }

    async def complete_session(self, session_id: str) -> dict:
        """Complete the session by sending client_id to recommendation service."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
            
        session = self.sessions[session_id]
        
        if session["client_id"] is None:
            raise ValueError("Cannot complete session without client ID")
        

        try:
            await self.agent_client.complete_session(session["client_id"])
            del self.sessions[session_id]
            return {"status": "success", "message": "Session completed"}
        except Exception as e:
            raise ValueError(f"Failed to complete session: {str(e)}")

    def add_recommendation(self, session_id: str, recommendation: dict):
        """Add a recommendation to the session."""
        if session_id in self.sessions:
            self.sessions[session_id]["recommendations"].append(recommendation)
            self.sessions[session_id]["last_update"] = datetime.now()