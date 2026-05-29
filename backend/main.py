# main.py
# Entry point for the FastAPI backend.
# Initialises the app, registers routes, and sets up the database.

import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.database.db import SessionLocal, init_db, migrate_db
from backend.database.seed_loader import load_seeds
from backend.routes import flashcards, library

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

# Initialise the FastAPI app
app = FastAPI(
    title="Wortblitz API",
    description="API for generating and studying German flashcards",
    version="1.0.0"
)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)

# Create tables, run column migrations, then load seed vocabulary
init_db()
migrate_db()
_db = SessionLocal()
try:
    load_seeds(_db)
finally:
    _db.close()

app.include_router(flashcards.router)
app.include_router(library.router)


@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    Used to verify the API is running correctly.
    """
    return {"status": "ok"}