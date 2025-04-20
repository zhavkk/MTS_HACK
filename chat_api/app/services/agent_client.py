import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

class AgentClient:
    def __init__(self):
        self.base_url = os.getenv("AGENT_SERVICE_URL", "http://agent-service:8001")
        self.callback_url = os.getenv("CALLBACK_URL", "http://backend:8000/callback")
        self.debug = os.getenv("DEBUG", "False").lower() == "true"

    async def send_user_message(self, user_id: str, text: str) -> None:
        """Send user message to recommendation service."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": {
                    "user_id": user_id,
                    "text": text
                }
            }
            async with session.post(
                f"{self.base_url}/last_message_user",
                json=payload,
                headers={"X-Callback-URL": self.callback_url}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to send user message: {await response.text()}")

    async def send_operator_message(self, text: str) -> None:
        """Send operator message to recommendation service."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "content": {
                    "text": text
                }
            }
            async with session.post(
                f"{self.base_url}/last_message_operator",
                json=payload,
                headers={"X-Callback-URL": self.callback_url}
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to send operator message: {await response.text()}")

    async def complete_session(self, user_id: str) -> None:
        """Complete the session by sending user_id to recommendation service."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "user_id": user_id
            }
            async with session.post(
                f"{self.base_url}/complete_session",
                json=payload
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to complete session: {await response.text()}")