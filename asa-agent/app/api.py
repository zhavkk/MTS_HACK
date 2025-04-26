from fastapi import APIRouter, HTTPException, status, Depends
from model import UserId, Knowledge, HistoryItem, SuggestionRequest, Answer, Response
from dotenv import load_dotenv
from redis import Redis, ConnectionError as RedisConnectionError
from logger import logger
from suggestion_service import generate_response

import os

router = APIRouter()
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")


def get_redis() -> Redis:
    """
    Подключение к Redis.
    """
    try:
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        redis_client.ping()
        return redis_client
    except ConnectionError as e:
        logger.error(f"[ASA-Agent] Не удалось подключиться к Redis: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis недоступен"
        )


@router.post("/suggest", response_model=Response, status_code=status.HTTP_200_OK)
async def suggest_response(user: UserId, redis: Redis = Depends(get_redis)) -> Response:
    """
    Получает данные из Redis (intent, emotion, knowledge) и генерирует ответ оператора.
    Сохраняет результат в Redis и возвращает в формате Response.
    """
    try:
        key_history = f"history:{user.user_id}"
        key_knowledge = f"knowledge:{user.user_id}"
        key_answer = f"answer:{user.user_id}"

        # Извлечение истории и ответа из базы знаний
        records_history = redis.lrange(key_history, -1, -1)
        records_knowledge = redis.lrange(key_knowledge, -1, -1)

        if not records_history or not records_knowledge:
            logger.warning(f"[ASA-Agent] Данные не найдены в Redis для пользователя {user.user_id}")
            raise HTTPException(status_code=404, detail="Данные не найдены в Redis")

        history = HistoryItem.parse_raw(records_history[0])
        knowledge = Knowledge.parse_raw(records_knowledge[0])

        logger.info(f"[ASA-Agent] История: {history}")
        logger.info(f"[ASA-Agent] Ответ из базы знаний: {knowledge}")

        request = SuggestionRequest(
            emotion=history.emotion,
            intent=history.intern,
            client_message=history.message,
            rag={"answer": knowledge.answer, "source": knowledge.source}
        )

        result = await generate_response(request)
        answer = Answer(answer=result["suggestion"])

        logger.info(f"[ASA-Agent] Сгенерированный ответ: {answer.answer}")
        redis.rpush(key_answer, answer.json())

        return Response(id=user.user_id, answer=answer.answer)

    except RedisConnectionError as e:
        logger.error(f"[ASA-Agent] Redis connection error: {e}")
        raise HTTPException(status_code=503, detail="Redis connection error")

    except Exception as e:
        logger.exception(f"[ASA-Agent] Внутренняя ошибка: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
