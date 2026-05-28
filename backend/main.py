# main.py
# Entry point for the FastAPI backend.
# Initialises the app, registers routes, and sets up the database.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.db import SessionLocal, init_db, migrate_db
from backend.database.seed_loader import load_seeds
from backend.routes import flashcards, library

# Initialise the FastAPI app
app = FastAPI(
    title="German Flashcard Agent API",
    description="API for generating and studying German flashcards",
    version="1.0.0"
)

# CORS middleware allows the React frontend to call this API.
# Without this the browser will block all requests from the frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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