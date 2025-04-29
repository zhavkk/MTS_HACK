
from model import HistoryItem, UserId, SummaryQAACombinedResponse
from logger import logger
import requests
from redis import Redis
from settings import RAG_URL, IE_URL, AS_URL, QSA_URL
from fastapi import HTTPException, status
import json


from pydantic import BaseModel, Field
from typing import List, Optional



class HistoryItem(BaseModel):
    role: str
    message: str
    emotion: Optional[str] = None
    intern:  Optional[str] = None

class Knowledge(BaseModel):
    answer: str
    source: Optional[str] = None

class BulkResponse(BaseModel):
    ans:       List[str]
    history:   List[HistoryItem]
    knowledge: List[Knowledge]


def call_rag(user:UserId):
    try:
        logger.info("call RAG")
        payload = {"user_id": user.user_id}
        resp = requests.post(RAG_URL, json=payload)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.info(f"Call_RAG - promlem:{e}")
        raise HTTPException(status_code=500, detail="Not found message in history")
        
def call_eia(user:UserId):
    logger.info("call EIA")
    payload = {"id": user.user_id}
    try:
        resp = requests.post(IE_URL, json=payload, timeout=5)
        resp.raise_for_status()
        return True
    except requests.HTTPError as e:
        # пробрасываем статус EIA как есть
        raise HTTPException(status_code=e.response.status_code,
                            detail=e.response.text)
    except requests.RequestException as e:
        raise HTTPException(status_code=502,
                            detail=f"EIA unreachable: {e}")
def call_as(user:UserId):
    try:
        logger.info("call AS")
        payload = {"user_id": user.user_id}
        resp = requests.post(AS_URL, json=payload)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.warning(f"Call_AS - promlem:{e}")
        raise HTTPException(status_code=500, detail="Not found message in history")

BACKEND_URL = "http://backend:8000/sessions/callback"

def call_backend(user: UserId, bulk: BulkResponse) -> bool:
    # берём последние элементы
    last_hist = bulk.history[-1]   if bulk.history   else None
    last_know = bulk.knowledge[-1] if bulk.knowledge else None
    last_ans  = bulk.ans[-1]       if bulk.ans       else ""

    payload = {
        "recommendation": {
            "link":      (last_know.source  if last_know else None),
            "intern":    (last_hist.intern  if last_hist else None),
            "know":      (last_know.answer  if last_know else None),
            "emotinal":  (last_hist.emotion if last_hist else None),
            "ans":       last_ans
        }
    }

    headers = {
        "Content-Type": "application/json",
        "X-Client-ID":  str(user.user_id)
    }

    try:
        logger.info(f"Sending callback to backend: {json.dumps(payload, ensure_ascii=False)}")
        resp = requests.post(BACKEND_URL, json=payload, headers=headers, timeout=8)
        resp.raise_for_status()
        logger.info(f"Backend callback OK (status {resp.status_code})")
        return True
    except requests.RequestException as e:
        logger.error(f"Call_BACKEND – problem: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Backend callback failed: {e}"
        )

def coplite_session(user: UserId, redis: Redis):
    try:
        logger.info("Sending callback to SQA – %s", user.user_id)
        resp = requests.post(QSA_URL, json={"user_id": user.user_id}, timeout=30)
        resp.raise_for_status()
        logger.info("Backend callback OK (status %s)", resp.status_code)

        key = f"feedback:{user.user_id}"
        raw = redis.lindex(key, -1)     
        if raw is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Summary not found",
            )

        return SummaryQAACombinedResponse.parse_raw(raw)
    except requests.RequestException as e:
        logger.error("CALL_QSA – problem: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"QSA callback failed: {e}",
        )
        
        


def prepross(user:UserId, redis: Redis):
    eia = call_eia(user)
    if not(eia):
        logger.warning("prepross some problems with eia")
        raise HTTPException(status_code=500, detail="Not found message in history")
    try:
        key = f"history:{user.user_id}"
        records = redis.lrange(key, -2, -1) 
        if len(records) <= 1:
            logger.info(f"user with id {user.user_id}, have one message on Redis")
            history_items = [HistoryItem.parse_raw(item) for item in records]
            rag = call_rag(user)
            if not(rag):
                logger.info(f"RAG - have some problems")
                raise HTTPException(status_code=500, detail="Not RAG")
            as_agent = call_as(user)
            if not(as_agent):
                logger.info(f"AS - have some problems")
                raise HTTPException(status_code=500, detail="Not AS")
            logger.info(f"call AS - success")
        else:
            history_items = [HistoryItem.parse_raw(item) for item in records]
            if history_items[-1].intern != history_items[-2].intern:
                logger.info(f"user with id {user.user_id}, INTERN NOT SAME: {history_items[-1].intern}, {history_items[-2].intern}")
                rag = call_rag(user)            
                as_agent = call_as(user)
                if not(as_agent):
                    logger.info(f"AS - have some problems")
                    raise HTTPException(status_code=500, detail="Not AS")
                logger.info(f"call AS - success")
            else:
                logger.info(f"user with id {user.user_id}, INTERN ARE SAME: {history_items[-1].intern}, {history_items[-2].intern}")

        raw_hist = redis.lrange(f"history:{user.user_id}",   0, -1)
        raw_know = redis.lrange(f"knowledge:{user.user_id}", 0, -1)
        raw_ans  = redis.lrange(f"answer:{user.user_id}",    0, -1)

        history_items   = [HistoryItem.model_validate_json(item) for item in raw_hist]
        knowledge_items = [Knowledge.model_validate_json(item)   for item in raw_know]

        # вытаскиваем именно строку ответа
        ans_list = [
            json.loads(item).get("answer", "")  # ← строка
            for item in raw_ans
        ]
        logger.info(f"backend aggregated")
        bulk = BulkResponse(
            ans       = ans_list,
            history   = history_items,
            knowledge = knowledge_items,
        )
        call_backend(user, bulk)
        return bulk
                        
                
    except Exception as e:
        logger.warning(f"Call_eis - promlem:{e}")
        raise HTTPException(status_code=500, detail="exeption")
                