from fastapi import FastAPI, HTTPException, status, Depends
from logger import logger
from api import router as api_router

import uvicorn

app = FastAPI(
    title="EIA Agent Service",
    description="Service for analyzing user messages to determine intent and emotion",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/eia-agent", tags=["api"])


@app.on_event("startup")
async def startup_event():
    logger.info("Starting EIA Agent application…")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down EIA Agent application…")


@app.get("/ping")
async def ping():
    logger.debug("Ping received")
    return {"pong": True}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)