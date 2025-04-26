from fastapi import FastAPI
from api import router as summary_qaa_router
from logger import logger

app = FastAPI(
    title="Summary & QAA Agent",
    description="Агент формирует краткое резюме диалога и проверяет соответствие общения стандартам",
    version="1.0.0"
)

app.include_router(summary_qaa_router, prefix="/api/sqa-agent", tags=["summary-sqa"])


@app.on_event("startup")
async def startup_event():
    logger.info("Summary + QAA Agent started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Summary + QAA Agent shutting down")


@app.get("/ping")
async def ping():
    return {"pong": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app",host="0.0.0.0" ,reload=True, port=8006)
