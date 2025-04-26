import os
import ssl
import aiohttp
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("MWS_API_KEY")
API_URL = "https://api.gpt.mws.ru/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

ASA_PROMPT = (
    "Ты специалист службы поддержки.\n"
    "На основе сообщения клиента, его эмоции и намерений, и также из найденной информации из базы знаний,\n"
    "сформируй предложение для оператора, как лучше всего ответить клиенту.\n\n"
    "Сформируй краткий, понятный и вежливый ответ клиенту от имени оператора. "
    "Не добавляй префиксов, просто ответь, как если бы ты писал человеку. "
    "Учитывай: эмоцию, намерение, найденный ответ и сообщение клиента.\n"
    "Если информация не соответствует намерению — вежливо это отметь и предложи альтернативу.\n"
    "Ответ должен быть вежливым, полезным и сочувствующим, особенно если эмоция негативная.\n"
    "Не продолжай, если уже дал полезный ответ."
)


def _get_connector() -> aiohttp.TCPConnector:
    """
    Создаёт TCPConnector с отключённым SSL (для dev-среды).
    """
    # Для production можно настроить SSL:
    # ssl_ctx = ssl.create_default_context(cafile="/path/to/ca.pem")
    # return aiohttp.TCPConnector(ssl=ssl_ctx)
    return aiohttp.TCPConnector(ssl=False)


_TIMEOUT = aiohttp.ClientTimeout(total=10)


async def fetch_response(session: aiohttp.ClientSession, payload: dict) -> str:
    """
    Выполняет запрос к LLM API и возвращает текст из ответа.
    """
    try:
        async with session.post(API_URL, headers=HEADERS, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                raise HTTPException(
                    status_code=resp.status,
                    detail=f"LLM service error: {error_text}"
                )
            data = await resp.json()
            return data["choices"][0]["message"]["content"]
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Network error connecting to LLM: {e}"
        )


async def generate_response(request) -> dict:
    """
    Генерирует рекомендованный ответ на основе эмоции, намерения и данных RAG.
    """
    user_message = (
        f"Эмоция клиента: {request.emotion}\n"
        f"Намерение клиента: {request.intent}\n"
        f"Сообщение клиента: {request.client_message}\n"
        f"Найденный ответ: {request.rag.get('answer', '')}\n"
        f"Ссылка: {request.rag.get('source', '')}"
    )

    payload = {
        "model": "qwen2.5-72b-instruct",
        "messages": [
            {"role": "system", "content": ASA_PROMPT},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.4,
        "max_tokens": 200,
        "stop": ["Спасибо за обращение.", "\n\n"],
    }

    connector = _get_connector()
    async with aiohttp.ClientSession(connector=connector, timeout=_TIMEOUT) as session:
        content = await fetch_response(session, payload)

    text = content.strip()
    # if len(text) < 20 or not any(
    #     w in text.lower() for w in ("ответ", "пожалуйста", "ссылка", "проверить")
    # ):
    #     return {"suggestion": "Модель не смогла сгенерировать полноценный ответ. "
    #         "Пожалуйста, проверьте информацию вручную или уточните запрос.\n"}

    return {"suggestion": f"Модель рекомендует ответить следующим образом:\n\n{text}"}
