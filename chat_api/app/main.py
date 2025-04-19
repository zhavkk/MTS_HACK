from fastapi import FastAPI
from .routers import sessions

app = FastAPI(title="Chat API")
app.include_router(sessions.router)