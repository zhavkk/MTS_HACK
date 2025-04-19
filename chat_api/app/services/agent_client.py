import httpx

class AgentClient:
    def __init__(self):
        self.agent_service_url = "http://agent-service/api/v1/process"
        self.crm_service_url = "http://crm-service/sessions"

    async def get_recommendations(self, messages: list[str]):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.agent_service_url,
                json={"messages": messages}
            )
            return response.json()["recommendations"]

    async def send_to_crm(self, data: dict):
        async with httpx.AsyncClient() as client:
            await client.post(
                self.crm_service_url,
                json=data
            )