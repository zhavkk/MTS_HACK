import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv
import time

load_dotenv()

API_URL = os.getenv("BCKEND_URL", "http://localhost:8000")
RECOMMENDATION_SERVICE_URL = os.getenv("RECOMMENDATION_SERVICE_URL", "http://localhost:8008")
CALLBACK_URL = os.getenv("CALLBACK_URL", "http://localhost:8000/callback")

async def create_session():
    """Create a new session."""
    async with aiohttp.ClientSession() as session:
        print("Creating new session...")
        async with session.post(f"{API_URL}/sessions") as response:
            if response.status == 200:
                data = await response.json()
                session_id = data["session_id"]
                print(f"Session created: {session_id}")
                return session_id
            else:
                print(f"Failed to create session: {await response.text()}")
                return None

async def send_user_message(session_id, message):
    """Send a user message to the session."""
    async with aiohttp.ClientSession() as session:
        print(f"Sending user message: {message}")
        payload = {
            "content": message,
            "role": "user"
        }
        async with session.post(
            f"{API_URL}/sessions/{session_id}/messages",
            json=payload
        ) as response:
            if response.status == 200:
                print("User message sent successfully")
                return True
            else:
                print(f"Failed to send user message: {await response.text()}")
                return False

async def send_operator_message(session_id, message):
    """Send an operator message to the session."""
    async with aiohttp.ClientSession() as session:
        print(f"Sending operator message: {message}")
        payload = {
            "content": message,
            "role": "operator"
        }
        async with session.post(
            f"{API_URL}/sessions/{session_id}/messages",
            json=payload
        ) as response:
            if response.status == 200:
                print("Operator message sent successfully")
                return True
            else:
                print(f"Failed to send operator message: {await response.text()}")
                return False

async def get_session_updates(session_id):
    """Get session updates including messages and recommendations."""
    async with aiohttp.ClientSession() as session:
        print(f"Getting updates for session: {session_id}")
        async with session.get(f"{API_URL}/sessions/{session_id}/updates") as response:
            if response.status == 200:
                data = await response.json()
                print("Session data:")
                print(f"Messages: {json.dumps(data['messages'], indent=2, ensure_ascii=False)}")
                print(f"Recommendations: {json.dumps(data['recommendations'], indent=2, ensure_ascii=False)}")
                return data
            else:
                print(f"Failed to get session updates: {await response.text()}")
                return None

async def complete_session(session_id):
    """Complete the session."""
    async with aiohttp.ClientSession() as session:
        print(f"Completing session: {session_id}")
        async with session.post(f"{API_URL}/sessions/{session_id}/complete") as response:
            if response.status == 200:
                print("Session completed successfully")
                return True
            else:
                print(f"Failed to complete session: {await response.text()}")
                return False

async def simulate_recommendation_callback(session_id, client_id, recommendation):
    """Simulate a callback from the recommendation service."""
    async with aiohttp.ClientSession() as session:
        print(f"Simulating recommendation callback for session: {session_id}")
        payload = {
            "recommendation": recommendation
        }
        headers = {
            "X-Client-ID": client_id
        }
        async with session.post(
            f"{API_URL}/sessions/callback",
            json=payload,
            headers=headers
        ) as response:
            if response.status == 200:
                print("Recommendation callback processed successfully")
                return True
            else:
                print(f"Failed to process recommendation callback: {await response.text()}")
                return False

async def get_session_client_id(session_id):
    """Get the client_id for a session."""
    async with aiohttp.ClientSession() as session:
        print(f"Getting client_id for session: {session_id}")
        async with session.get(f"{API_URL}/sessions/{session_id}") as response:
            if response.status == 200:
                data = await response.json()
                client_id = data["client_id"]
                print(f"Client ID: {client_id}")
                return client_id
            else:
                print(f"Failed to get client_id: {await response.text()}")
                return None

async def test_full_conversation():
    """Test a full conversation flow."""
    print("=== Starting full conversation test ===")
    
    # Step 1: Create a session
    session_id = await create_session()
    if not session_id:
        print("Test failed: Could not create session")
        return
    
    # Step 2: Get the client_id for the session
    client_id = await get_session_client_id(session_id)
    if not client_id:
        print("Test failed: Could not get client_id")
        return
    
    # Step 3: Send a user message
    user_message = "Здравствуйте, у меня проблема с интернетом"
    if not await send_user_message(session_id, user_message):
        print("Test failed: Could not send user message")
        return
    
    # Step 4: Simulate recommendation callback
    recommendation = {
        "link": "https://example.com/internet-troubleshooting",
        "intern": "user",
        "know": "Проверьте подключение к интернету",
        "emotinal": "neutral",
        "ans": "Проверьте подключение к интернету и перезагрузите роутер"
    }
    if not await simulate_recommendation_callback(session_id, client_id, recommendation):
        print("Test failed: Could not simulate recommendation callback")
        return
    
    # Step 5: Get session updates
    session_data = await get_session_updates(session_id)
    if not session_data:
        print("Test failed: Could not get session updates")
        return
    
    # Step 6: Send an operator message
    operator_message = "Здравствуйте! Расскажите, пожалуйста, подробнее о проблеме."
    if not await send_operator_message(session_id, operator_message):
        print("Test failed: Could not send operator message")
        return
    
    # Step 7: Simulate another recommendation callback
    recommendation = {
        "link": "https://example.com/operator-guidelines",
        "intern": "operator",
        "know": "Задайте уточняющие вопросы о проблеме",
        "emotinal": "neutral",
        "ans": "Спросите пользователя о времени возникновения проблемы и попытках её решения"
    }
    if not await simulate_recommendation_callback(session_id, client_id, recommendation):
        print("Test failed: Could not simulate recommendation callback")
        return
    
    # Step 8: Get session updates again
    session_data = await get_session_updates(session_id)
    if not session_data:
        print("Test failed: Could not get session updates")
        return
    
    # Step 9: Complete the session
    if not await complete_session(session_id):
        print("Test failed: Could not complete session")
        return
    
    print("=== Full conversation test completed successfully ===")

if __name__ == "__main__":
    asyncio.run(test_full_conversation()) 