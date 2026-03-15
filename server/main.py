import sys
from pathlib import Path

# Ensure the project root (parent of `server/`) is on sys.path so that
# `src.*` packages are importable regardless of the working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.agents import agent_manager
from router.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Place startup initialization logic here.
    print("FastAPI service started.")
    yield
    # Place shutdown cleanup logic here.
    print("FastAPI service stopped.")


app = FastAPI(
    title="multi-agent-s2c",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/", tags=["health"])
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
