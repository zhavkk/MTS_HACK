import asyncio
from datetime import datetime, timedelta
from collections import defaultdict
import uuid

class MessageBuffer:
    def __init__(self):
        self.sessions = defaultdict(dict)
        self.timeout = 10  

    def create_session(self):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "messages": [],
            "recommendations": [],
            "created_at": datetime.now(),
            "timer": None
        }
        return session_id

    async def add_message(self, session_id: str, message: str):
        session = self.sessions[session_id]
        session["messages"].append({
            "content": message,
            "timestamp": datetime.now()
        })
        
        if session["timer"]:
            session["timer"].cancel()
        
        session["timer"] = asyncio.create_task(
            self._process_buffered(session_id)
        )

    async def _process_buffered(self, session_id: str):
        await asyncio.sleep(self.timeout)
        messages = self._get_messages(session_id)
        recommendations = await agent_client.get_recommendations(messages)
        
        self.sessions[session_id]["recommendations"].extend(recommendations)
        self.sessions[session_id]["timer"] = None

    def _get_messages(self, session_id: str):
        return [msg["content"] for msg in self.sessions[session_id]["messages"]]

    def get_session_data(self, session_id: str):
        return self.sessions[session_id]