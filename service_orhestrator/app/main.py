from fastapi import FastAPI, HTTPException
from api import router
from logger import logger
import uvicorn


app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting application…")

@app.get("/ping")
async def ping():
    logger.debug("Ping received")
    return {"pong": True}

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application…")


app.include_router(router, prefix="/api/orhestrator", tags=["api"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8008, reload=True)