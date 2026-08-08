# -----------------------------------------------------------------
# main.py
#
# The entry point of the FastAPI application. It creates the app,
# allows the React frontend to call it (CORS), creates the SQLite
# database tables on startup, and plugs in every router.
#
# Run from the PROJECT ROOT (the folder that contains "backend/",
# "agents/", "router/", "rag/") with:
#   uvicorn backend.app.main:app --reload
# -----------------------------------------------------------------

import os
import sys

# Makes "backend/" importable as top-level "app", on top of the project
# root that's already importable (needed for "from app.config import ..."
# below, and for every other backend file that does "from app.something").
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_ORIGIN
from app.database import init_db
from app.routers import auth, chat, conversations, profile

app = FastAPI(
    title="CampusMate API",
    description="Backend for the CampusMate student assistant capstone project.",
    version="1.0.0",
)

# Allows the React frontend (running on a different port) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# Every router already defines its own "/api/..." prefix (see routers/*.py).
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/")
def health_check():
    """Simple route to check the API is running. Visit /docs for the full API."""
    return {"status": "ok", "message": "CampusMate API is running"}
