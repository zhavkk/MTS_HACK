from fastapi import FastAPI
from api import router
from logger import logger
import uvicorn

app = FastAPI(
    title="ASA Agent Service",
    description="Action Suggestion Agent: генерирует рекомендации оператору на основе намерения, эмоции и ответа из базы знаний",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    logger.info("[ASA Agent] Приложение запущено")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("[ASA Agent] Приложение остановлено")


@app.get("/ping")
async def ping():
    logger.debug("[ASA Agent] Ping получен")
    return {"pong": True}

app.include_router(router, prefix="/api/asa-agent", tags=["asa"])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)
