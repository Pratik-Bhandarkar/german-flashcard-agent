# flashcards.py
# Defines all HTTP endpoints for flashcard operations.
# Handles fetching, processing, updating and deleting flashcards.

import shutil
import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.models import Flashcard
from pipeline.graph import run_pipeline

# APIRouter groups all flashcard endpoints together.
# The prefix means every route here starts with /flashcards.
router = APIRouter(prefix="/flashcards", tags=["flashcards"])

# Temporary folder for uploaded files during processing
UPLOAD_FOLDER = Path("data/uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


# --- Request/Response Models ---
# Pydantic models define the shape of request bodies and responses.
# FastAPI uses these for automatic validation and documentation.

class UpdateFlashcardRequest(BaseModel):
    """Request body for updating a flashcard."""
    difficulty: str | None = None
    next_review: str | None = None
    german_word: str | None = None
    mnemonic: str | None = None
    tags: list[str] | None = None


class ProcessRequest(BaseModel):
    """Request body for processing plain text input."""
    text: str
    source: str = "manual input"
    tags: list[str] = []


# --- Endpoints ---

@router.get("")
def get_all_flashcards(db: Session = Depends(get_db)):
    """
    Returns all flashcards ordered by creation date.
    Used by the study UI to load the full card deck.
    """
    flashcards = db.query(Flashcard).order_by(
        Flashcard.created_at.desc()
    ).all()
    return [card.to_dict() for card in flashcards]


@router.get("/review")
def get_cards_due_for_review(db: Session = Depends(get_db)):
    """
    Returns only flashcards due for review today or earlier.
    Used by the spaced repetition study mode.
    """
    today = date.today().isoformat()
    flashcards = db.query(Flashcard).filter(
        Flashcard.next_review <= today
    ).all()
    return [card.to_dict() for card in flashcards]


@router.get("/{flashcard_id}")
def get_flashcard(flashcard_id: str, db: Session = Depends(get_db)):
    """
    Returns a single flashcard by ID.
    Raises 404 if the card doesn't exist.
    """
    card = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    return card.to_dict()


@router.post("/process/text")
def process_text(request: ProcessRequest, db: Session = Depends(get_db)):
    """
    Runs the full pipeline on plain text input.
    Returns the newly created flashcards.
    """
    final_state = run_pipeline(
        input_type="text",
        input_data=request.text,
        source=request.source,
        tags=request.tags
    )

    saved_count = final_state["storage_result"]["saved"]
    return {
        "message": f"Successfully created {saved_count} flashcards",
        "saved": saved_count,
        "skipped": final_state["storage_result"]["skipped"],
        "flashcards": final_state["enrichment_result"]["flashcards"]
    }


@router.post("/process/image")
async def process_image(
    file: UploadFile = File(...),
    source: str = "image upload",
    db: Session = Depends(get_db)
):
    """
    Accepts an image upload and runs the full pipeline on it.
    Saves the file temporarily, processes it, then deletes it.
    """
    # Save uploaded file temporarily with a unique name
    temp_path = UPLOAD_FOLDER / f"{uuid.uuid4()}_{file.filename}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        final_state = run_pipeline(
            input_type="image",
            input_data=str(temp_path),
            source=source,
        )

        saved_count = final_state["storage_result"]["saved"]
        return {
            "message": f"Successfully created {saved_count} flashcards",
            "saved": saved_count,
            "skipped": final_state["storage_result"]["skipped"],
        }

    finally:
        # Always delete the temp file even if processing fails
        if temp_path.exists():
            temp_path.unlink()


@router.put("/{flashcard_id}")
def update_flashcard(
    flashcard_id: str,
    request: UpdateFlashcardRequest,
    db: Session = Depends(get_db)
):
    """
    Updates specified fields on a flashcard.
    Used for updating difficulty after studying or editing content.
    """
    card = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    # Only update fields that were actually provided in the request
    if request.difficulty is not None:
        card.difficulty = request.difficulty
    if request.next_review is not None:
        card.next_review = request.next_review
    if request.german_word is not None:
        card.german_word = request.german_word
    if request.mnemonic is not None:
        card.mnemonic = request.mnemonic
    if request.tags is not None:
        card.tags = request.tags

    db.commit()
    return card.to_dict()


@router.delete("/{flashcard_id}")
def delete_flashcard(flashcard_id: str, db: Session = Depends(get_db)):
    """
    Deletes a flashcard permanently.
    Returns 404 if the card doesn't exist.
    """
    card = db.query(Flashcard).filter(
        Flashcard.id == flashcard_id
    ).first()

    if not card:
        raise HTTPException(status_code=404, detail="Flashcard not found")

    db.delete(card)
    db.commit()

    return {"message": f"Flashcard {flashcard_id} deleted successfully"}