from fastapi import HTTPException, status, Depends, APIRouter
from aiohttp import TCPConnector
import aiohttp
from logic import fetch_result, EMOTION_PROMPT, INTENT_PROMPT
from model import User, HistoryItem, Response
from logger import logger
from redis import Redis
import os
from dotenv import load_dotenv
import asyncio

router = APIRouter()

load_dotenv()

REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_HOST = os.getenv("REDIS_HOST")


def get_redis() -> Redis:
    """
    Устанавливает соединение с Redis.
    Возвращает Redis-клиент или возбуждает исключение при ошибке подключения.
    """
    try:
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        redis_client.ping()
        return redis_client
    except ConnectionError as e:
        logger.error(f"❌ Не удалось подключиться к Redis: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@router.post("/analyze", response_model=Response, status_code=status.HTTP_200_OK)
async def analyze_message(request: User, redis: Redis = Depends(get_redis)) -> Response:
    """
    Обрабатывает последнее сообщение пользователя:
    - Извлекает из Redis последнее сообщение по ID
    - Определяет настроение и намерение
    - Обновляет историю Redis с новыми данными
    """
    try:
        key = f"history:{request.id}"
        records = redis.lrange(key, -1, -1)

        if not records:
            logger.warning(f"⚠️ История пуста для user-{request.id}")
            raise HTTPException(status_code=400, detail="History is empty")

        user_message = HistoryItem.parse_raw(records[0]).message
        logger.info(f"📨 user-{request.id} message: {user_message}")

        if not user_message:
            logger.warning(f"❌ Сообщение не найдено для user-{request.id}")
            raise HTTPException(status_code=400, detail="Message not found in history")

        connector = TCPConnector(ssl=False)

        async with aiohttp.ClientSession(connector=connector) as session:
            emotion_task = fetch_result(session, EMOTION_PROMPT, user_message)
            intent_task = fetch_result(session, INTENT_PROMPT, user_message)
            emotion_result, intent_result = await asyncio.gather(emotion_task, intent_task)

        logger.info(
            f"✅ user-{request.id} — emotion: {emotion_result['emotion']}, "
            f"intent: {intent_result['intent']}"
        )

        new_history_item = HistoryItem(
            role="user",
            message=user_message,
            emotion=emotion_result["emotion"],
            intern=intent_result["intent"]
        )

        redis.lset(key, -1, new_history_item.json())
        logger.info(f"💾 История обновлена для user-{request.id}")

        return Response(user_id=request.id, message="Successfully done")

    except aiohttp.ClientError as e:
        logger.error(f"🌐 Ошибка сети: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Network error: {str(e)}")

    except Exception as e:
        logger.error(f"🔥 Внутренняя ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
