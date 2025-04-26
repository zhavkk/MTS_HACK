# app/api.py
from fastapi import APIRouter, HTTPException, status, Depends
from redis import Redis, ConnectionError as RedisConnectionError
from model import DialogueRequest, SummaryQAACombinedResponse, Message
from logic import analyze_dialogue
from logger import logger
import json
from dotenv import load_dotenv
import os

load_dotenv()
router = APIRouter()

REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_HOST = os.getenv("REDIS_HOST")


def get_redis():
    try:
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        redis_client.ping()
        return redis_client
    except ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


@router.post("/summarise", response_model=SummaryQAACombinedResponse, status_code=status.HTTP_200_OK)
async def evaluate_summary_and_quality(request: DialogueRequest, redis: Redis = Depends(get_redis)):
    key = f"history:{request.user_id}"
    records = redis.lrange(key, 0, -1)

    if not records:
        raise HTTPException(status_code=404, detail="History is empty")

    dialogue = [
    Message(role=rec["role"], content=rec["message"])
    for rec in map(json.loads, records)
    ]   

    try:
        result = await analyze_dialogue(dialogue)
        result_key = f"feedback:{request.user_id}"
        redis.set(result_key, result.json())

        return result
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
