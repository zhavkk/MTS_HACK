from fastapi import APIRouter, HTTPException, status, Depends
from logger import logger
from logic import get_answer_from_intent
from redis import Redis, ConnectionError as RedisConnectionError
from dotenv import load_dotenv
from model import UserId, HistoryItem, Knowledge, Response
import os

load_dotenv()

router = APIRouter()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")

def get_redis() -> Redis:
    """
    Подключение к Redis и проверка соединения.
    """
    try:
        client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping()
        return client
    except RedisConnectionError as e:
        logger.error(f"[Redis] Connection error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Redis недоступен")



@router.post("/search", response_model=Response, status_code=status.HTTP_200_OK)
def search_knowledge(user: UserId, redis: Redis = Depends(get_redis)):
    """
    Извлекает последнее намерение из Redis и возвращает ответ из RAG (KnowledgeAgent).
    """
    try:
        key = f"history:{user.user_id}"
        logger.info(f"[KnowledgeAgent] Запрос от пользователя {user.user_id}")

        items = redis.lrange(key, -1, -1)
        if not items:
            logger.warning(f"[KnowledgeAgent] История пуста: {user.user_id}")
            raise HTTPException(status_code=404, detail="История пользователя не найдена")

        history_item = HistoryItem.parse_raw(items[0])
        intent = history_item.intern

        if not intent:
            logger.warning(f"[KnowledgeAgent] Не найден intent для пользователя {user.user_id}")
            raise HTTPException(status_code=400, detail="Намерение отсутствует в истории")

        result = get_answer_from_intent(intent)

        if not result.answer:
            logger.warning(f"[KnowledgeAgent] Не найден ответ по intent: {intent}")
            raise HTTPException(status_code=404, detail="Ответ не найден")

        knowledge = Knowledge(answer=result.answer, source=result.source)
        redis_key = f"knowledge:{user.user_id}"
        redis.rpush(redis_key, knowledge.json())

        logger.info(f"[KnowledgeAgent] Ответ сохранён: {knowledge.answer}\n"
                    f"Sources - {knowledge.source}")
        return Response(user_id=user.user_id, message=knowledge)

    except Exception as e:
        logger.exception(f"[KnowledgeAgent] Внутренняя ошибка: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")
    
