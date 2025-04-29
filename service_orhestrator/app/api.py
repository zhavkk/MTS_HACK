from fastapi import APIRouter, Depends, HTTPException, status
from model import LastMessage, Response, HistoryItem, HistoryResponse, UserId,  KnowledgeHistoryItem, Knowledge, ListAnswer, Answer, SummaryQAACombinedResponse
from dotenv import load_dotenv
from redis import Redis, ConnectionError as RedisConnectionError
from logger import logger
from logic import prepross, coplite_session
from typing import List
import os

router = APIRouter()
load_dotenv()

REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_HOST = os.getenv("REDIS_HOST")



N = os.getenv("MAX_USER_LAST_MESSAGE")

"""
ROUTES
1)  last_message - POST
2)  get_history - GET
3)  update_internt_emotional  - POST
# -  get_all_dialogues - GET
"""

def get_redis():
    try:
        redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        redis_client.ping()  # Проверка подключения
        return redis_client
    except RedisConnectionError as e:
        logger.error(f"Не удалось подключиться к Redis: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

@router.post(
    "/last_message_user",
    response_model=Response,
    tags=["Messages"],
    summary="Save the user's last message",
    description=(
        "Pushes the latest text coming from the **user** into the Redis history "
        "list (`history:{user_id}`) and triggers the preprocessing pipeline."
    ),
)
def last_message_user(message: LastMessage, r: Redis = Depends(get_redis)):
    """Persist the user's message and start preprocessing."""
    try:
        key = f"history:{message.content.user_id}"
        item = HistoryItem(role="user", message=message.content.text)
        r.rpush(key, item.json())
        logger.info(
            "user with id %s sent message: %s", message.content.user_id, message.content.text
        )
        prepross(UserId(user_id=message.content.user_id), r)
        return Response(response="Message successfully pre‑processed (user)")
    except HTTPException as http_exc:
        logger.error("HTTPException: %s", http_exc.detail)
        raise http_exc


@router.post(
    "/last_messag_operator",
    response_model=Response,
    tags=["Messages"],
    summary="Save the operator's last message",
    description=(
        "Logs a text sent **by the operator** into the Redis history list "
        "(`history:{user_id}`). The preprocessing pipeline is _not_ launched."
    ),
)
def last_message_operator(message: LastMessage, r: Redis = Depends(get_redis)):
    """Persist the operator's message."""
    try:
        key = f"history:{message.content.user_id}"
        item = HistoryItem(role="operator", message=message.content.text)
        r.rpush(key, item.json())
        logger.info(
            "operator with user_id - %s sent message: %s", message.content.user_id, message.content.text
        )
        # Preprocessing deliberately skipped for operator messages
        return Response(response="Message successfully recorded (operator)")
    except HTTPException as http_exc:
        logger.error("HTTPException: %s", http_exc.detail)
        raise http_exc

# ---------------------------------------------------------------------------
#  Sessions ──────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.post(
    "/complete_session",
    response_model=List[SummaryQAACombinedResponse],
    tags=["Sessions"],
    summary="Generate a consolidated session summary",
    description="Returns a combined Q&A summary for the entire user session that is stored in Redis.",
)
def complete(message: UserId, r: Redis = Depends(get_redis)):
    """Return a compiled Q&A summary for the given user session."""
    try:
        ans = coplite_session(message, r)
        return ans
    except HTTPException as http_exc:
        logger.error("HTTPException: %s", http_exc.detail)
        raise http_exc

# ---------------------------------------------------------------------------
#  Answers (LLM responses) ───────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.get(
    "/history_ans/{user_id}",
    response_model=ListAnswer,
    tags=["Answers"],
    summary="Get answer history",
    description="Fetches the list of answers generated for a given `user_id`.",
)
async def get_history_answers(user_id: int, r: Redis = Depends(get_redis)):
    """Retrieve all answer records (AI responses) for a user."""
    try:
        key = f"answer:{user_id}"
        history = r.lrange(key, 0, -1)
        if not history:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History not found")
        logger.info("Retrieved answer history for user %s", user_id)
        history_items = [Answer.parse_raw(item) for item in history]
        return ListAnswer(answers=history_items)
    except HTTPException as http_exc:
        logger.error("HTTPException: %s", http_exc.detail)
        raise http_exc


@router.delete(
    "/history_ans/{user_id}",
    response_model=ListAnswer,
    status_code=status.HTTP_200_OK,
    tags=["Answers"],
    summary="Delete answer history and return the removed items",
    description="Deletes all answers for the specified `user_id` and returns the removed records.",
)
async def delete_history_answers(user_id: int, r: Redis = Depends(get_redis)):
    """Delete and return the answer history for the user."""
    key = f"answer:{user_id}"
    history = r.lrange(key, 0, -1)
    if not history:
        logger.warning("No history to delete for user %s", user_id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History not found")

    history_items = [Answer.parse_raw(item) for item in history]
    r.delete(key)
    logger.info("Deleted answer history for user %s", user_id)
    return ListAnswer(answers=history_items)

# ---------------------------------------------------------------------------
#  Intent / Emotion ──────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.post(
    "/update_intent_emotional",
    response_model=HistoryResponse,
    tags=["Intent"],
    summary="Update user intent & emotion",
    description=(
        "Compares the last two history records to detect a change in intent or emotion. "
        "If a change is detected, a knowledge‑agent could be triggered (TODO)."
    ),
)
async def update_intent_emotional(user: UserId, r: Redis = Depends(get_redis)):
    """Detect changes in the user's intent/emotion and (optionally) trigger the knowledge agent."""
    try:
        key = f"history:{user.user_id}"
        records = r.lrange(key, -2, -1)
        if len(records) <= 1:
            logger.info("user %s has only one history record", user.user_id)
            history_items = [HistoryItem.parse_raw(item) for item in records]
            # TODO: call Knowledge agent
        else:
            history_items = [HistoryItem.parse_raw(item) for item in records]
            if history_items[-1].intern != history_items[-2].intern:
                logger.info(
                    "user %s, INTENT CHANGED: %s → %s",
                    user.user_id,
                    history_items[-2].intern,
                    history_items[-1].intern,
                )
                # TODO: call Knowledge agent
            else:
                logger.info(
                    "user %s, INTENT UNCHANGED: %s",
                    user.user_id,
                    history_items[-1].intern,
                )
        return HistoryResponse(response=history_items)
    except HTTPException as http_exc:
        logger.error("HTTPException: %s", http_exc.detail)
        raise http_exc

# ---------------------------------------------------------------------------
#  History (messages) ────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.delete(
    "/delete_user",
    response_model=Response,
    tags=["History"],
    summary="Delete all message history for a user",
    description="Removes the entire `history:{user_id}` list from Redis.",
)
async def delete_user_history(user: UserId, r: Redis = Depends(get_redis)):
    """Completely remove a user's message history from Redis."""
    try:
        key = f"history:{user.user_id}"
        r.delete(key)
        if not r.exists(key):
            logger.info("History for user %s deleted successfully", user.user_id)
        else:
            logger.error("Failed to delete history for user %s", user.user_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete history")
        return Response(response="Successfully deleted history")
    except HTTPException as http_exc:
        logger.error("HTTPException: %s", http_exc.detail)
        raise http_exc


@router.get(
    "/history/{user_id}",
    response_model=HistoryResponse,
    tags=["History"],
    summary="Get full message history",
    description="Returns the complete message history (`history:{user_id}`) for a user.",
)
async def get_history(user_id: int, r: Redis = Depends(get_redis)):
    """Retrieve the full message history for a user."""
    try:
        key = f"history:{user_id}"
        history = r.lrange(key, 0, -1)
        if not history:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="History not found")
        logger.info("Retrieved history for user %s", user_id)
        history_items = [HistoryItem.parse_raw(item) for item in history]
        return HistoryResponse(response=history_items)
    except HTTPException as http_exc:
        logger.error("HTTPException: %s", http_exc.detail)
        raise http_exc

# ---------------------------------------------------------------------------
#  Knowledge ────────────────────────────────────────────────────────────────
# ---------------------------------------------------------------------------

@router.get(
    "/history_knowledge/{user_id}",
    response_model=KnowledgeHistoryItem,
    tags=["Knowledge"],
    summary="Get knowledge history",
    description="Fetches the knowledge entries stored for the specified user.",
)
async def get_knowledge(user_id: int, r: Redis = Depends(get_redis)):
    """Retrieve the knowledge history for a user."""
    try:
        key = f"knowledge:{user_id}"
        history = r.lrange(key, 0, -1)
        if not history:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge not found")
        logger.info("Retrieved knowledge history for user %s", user_id)
        history_items = [Knowledge.parse_raw(item) for item in history]
        return KnowledgeHistoryItem(knowledge=history_items)
    except HTTPException as http_exc:
        logger.error("HTTPException: %s", http_exc.detail)
        raise http_exc


@router.delete(
    "/delete_knowledge/{user_id}",
    response_model=Response,
    tags=["Knowledge"],
    summary="Delete knowledge history",
    description="Deletes the entire knowledge list (`knowledge:{user_id}`) for a user.",
)
async def delete_knowledge(user_id: int, r: Redis = Depends(get_redis)):
    """Delete all stored knowledge for a user."""
    try:
        key = f"knowledge:{user_id}"
        r.delete(key)
        if not r.exists(key):
            logger.info("Knowledge for user %s deleted successfully", user_id)
        else:
            logger.error("Failed to delete knowledge for user %s", user_id)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete knowledge")
        return Response(response="Successfully deleted knowledge")
    except HTTPException as http_exc:
        logger.error("HTTPException: %s", http_exc.detail)
        raise http_exc
