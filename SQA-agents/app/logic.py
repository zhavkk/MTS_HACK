import asyncio
import json
import os
from typing import List

import aiohttp
from fastapi import HTTPException
from pydantic import ValidationError

from model import Message, SummaryQAACombinedResponse
from summary_qaa_config import SUMMARY_PROMPT, QAA_PROMPT

MWS_URL = "https://api.gpt.mws.ru/v1/chat/completions"
MWS_API_KEY = os.getenv("MWS_API_KEY")
HEADERS = {
    "Authorization": f"Bearer {MWS_API_KEY}",
    "Content-Type": "application/json",
}

async def fetch_json_result(
    session: aiohttp.ClientSession,
    prompt: str,
    user_message: str,
    model: str = "qwen2.5-72b-instruct",
) -> dict:
    """Отправляет один промпт в MWS и возвращает JSON‑ответ модели."""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.4,
        "max_tokens": 300,
        "stop": ["\n\n"],
    }

    async with session.post(MWS_URL, headers=HEADERS, json=payload) as resp:
        if resp.status != 200:
            raise HTTPException(status_code=resp.status, detail=await resp.text())

        raw = await resp.json()
        content = raw["choices"][0]["message"]["content"]

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Невалидный JSON от модели")


async def analyze_dialogue(dialogue: List[Message]) -> SummaryQAACombinedResponse:
    """Параллельно запрашивает summary и QAA, валидирует, объединяет."""
    formatted = "\n".join(f"{m.role.capitalize()}: {m.content}" for m in dialogue)

    connector = aiohttp.TCPConnector(ssl=False)  # если нужен self‑signed SSL
    async with aiohttp.ClientSession(connector=connector) as session:
        summary_coro = fetch_json_result(session, SUMMARY_PROMPT, formatted)
        qaa_coro = fetch_json_result(session, QAA_PROMPT, formatted)
        summary_json, quality_json = await asyncio.gather(summary_coro, qaa_coro)

    try:
        combined = SummaryQAACombinedResponse.model_validate(
            {"summary": summary_json, "quality_review": quality_json}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM вернул некорректную схему: {e}",
        ) from e

    return combined