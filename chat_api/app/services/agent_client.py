import aiohttp
import os
from dotenv import load_dotenv
import asyncio
load_dotenv()

class AgentClient:
    def __init__(self):
        self.base_url = "http://orchestrator:8008/api/orhestrator" 
        self.callback_url = os.getenv("CALLBACK_URL", "http://backend:8000/sessions/callback")
        self.debug = os.getenv("DEBUG", "False").lower() == "true"

    async def send_user_message(self, user_id: str, text: str) -> None:
        """Send user message to recommendation service."""

        async with aiohttp.ClientSession() as session:
            payload = {
                "content": {
                    "text": text,
                    "user_id": user_id
                }
            }
            headers = {
                "X-Callback-URL": self.callback_url,
                "X-Client-ID": user_id
            }

            async with session.post(
                f"{self.base_url}/last_message_user",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to send user message: {await response.text()}")

    async def send_operator_message(self, user_id: str, text: str) -> None:
        """Send operator message to recommendation service."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": {
                    "text": text,
                    "user_id": user_id 
                }
            }
            headers = {
                "X-Callback-URL": self.callback_url
            }
            print(f"Sending operator message to recommendation service: {payload}")

            
            async with session.post(
                f"{self.base_url}/last_message_operator",
                json=payload,
                headers=headers
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to send operator message: {await response.text()}")

    async def complete_session(self, user_id: str) -> None:
        """Complete the session by sending user_id to recommendation service."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": {
                    "text": "session_complete",
                    "user_id": user_id
                },
                "emotion": "neutral",
                "intern": "complete" 
            }
            async with session.post(
                f"{self.base_url}/complete_session",
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to complete session: {await response.text()}")