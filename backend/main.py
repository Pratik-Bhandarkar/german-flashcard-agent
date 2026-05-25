# main.py
# Entry point for the FastAPI backend.
# Initialises the app, registers routes, and sets up the database.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.db import init_db
from backend.routes import flashcards

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

# Create database tables on startup if they don't exist
init_db()

# Register the flashcards router — all /flashcards routes live there
app.include_router(flashcards.router)


@app.get("/health")
def health_check():
    """
    Simple health check endpoint.
    Used to verify the API is running correctly.
    """
    return {"status": "ok"}