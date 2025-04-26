from fastapi import FastAPI
from api import router
from logger import logger
import uvicorn


app = FastAPI(
    title="RAG Agent Service",
    description="Service for retrieving relevant answers based on detected intents using FAISS and vector embeddings.",
    version="1.0.0"
)

app.include_router(router, prefix="/api/rag-agent", tags=["rag-agent"])


@app.on_event("startup")
async def startup_event():
    logger.info("RAG Agent starting...")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("RAG Agent shutting down...")


@app.get("/ping")
async def ping():
    logger.debug("Ping received")
    return {"pong": True}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
