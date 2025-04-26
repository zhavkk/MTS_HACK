import os
import json
from fastapi import HTTPException
from dotenv import load_dotenv
from aiohttp import ClientSession

load_dotenv()

API_KEY = os.getenv("MWS_API_KEY")
API_URL = "https://api.gpt.mws.ru/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

ALL_INTENTS = [
    "billing", "payment_issue", "refund_request", "autopay_management", "bonus_program",
    "internet_issue", "home_internet_issue", "connectivity_diagnostics", "data_package_management",
    "sim_management", "e_sim_activation", "sim_blocking", "number_freeze",
    "subscription_cancel", "plan_change", "usage_details",
    "account_access_issue", "account_management", "personal_data_update", "delete_account",
    "call_request", "appointment_request",
    "information_request", "complaint", "feedback", "technical_request", "account_termination",
    "greeting", "goodbye", "other"
]

EMOTION_PROMPT = (
    "Ты специалист службы поддержки. "
    "Твоя задача — определить настроение клиента по его сообщению. "
    "Разрешено выбирать только одно значение из следующего списка:\n"
    "[positive, polite, neutral, polite_dissatisfaction, irritation, anger, surprise, "
    "disappointment, sadness, anxiety, outrage].\n\n"
    "Ответ строго в формате JSON:\n"
    "{ \"emotion\": \"<одно из списка>\" }\n"
    "Не добавляй ничего, кроме JSON."

)

INTENT_PROMPT = (
    "Ты специалист службы поддержки. "
    "Твоя задача — определить намерение клиента по его сообщению. "
    "Выбери одно из следующих намерений:\n"
    f"[{', '.join(ALL_INTENTS)}]\n\n"
    "Ответ верни строго в формате JSON:\n"
    "{ \"intent\": \"<одно из списка>\" }\n"
    "Не добавляй ничего, кроме JSON."
)


async def fetch_result(
        session: ClientSession,
        prompt: str,
        user_message: str,
        model: str = "mws-gpt-alpha"
) -> dict:
    """
    Отправляет запрос к LLM и возвращает JSON-ответ.
    """
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.2,
        "max_tokens": 60,
        "stop": ["\n"]
    }

    async with session.post(API_URL, headers=HEADERS, json=payload, ssl=False) as response:
        if response.status != 200:
            raise HTTPException(status_code=response.status, detail=await response.text())

        data = await response.json()
        content = data["choices"][0]["message"]["content"]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Невалидный JSON от модели")