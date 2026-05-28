# flashcards.py
# Defines all HTTP endpoints for flashcard operations.
# Handles fetching, processing, updating and deleting flashcards.

import shutil
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.models import Flashcard
from pipeline.graph import run_pipeline
from pipeline.tools import deepl_client

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

UPLOAD_FOLDER = Path("data/uploads")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".pdf"}

_TAG_MAX_ITEMS = 50
_TAG_MAX_LEN = 100


class UpdateFlashcardRequest(BaseModel):
    difficulty: Literal["easy", "medium", "hard"] | None = None
    next_review: str | None = None
    german_word: str | None = Field(default=None, max_length=200)
    mnemonic: str | None = Field(default=None, max_length=2000)
    tags: Annotated[list[str], Field(max_length=_TAG_MAX_ITEMS)] | None = None

    @field_validator("next_review")
    @classmethod
    def validate_date(cls, v):
        if v is None:
            return v
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("next_review must be an ISO date string (YYYY-MM-DD)")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v is None:
            return v
        for tag in v:
            if len(tag) > _TAG_MAX_LEN:
                raise ValueError(f"Each tag must be at most {_TAG_MAX_LEN} characters")
        return v


class ProcessRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)
    source: str = Field(default="manual input", max_length=200)
    tags: Annotated[list[str], Field(max_length=_TAG_MAX_ITEMS)] = []


class TranslateTextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)


class TranslationRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)
    tags: Annotated[list[str], Field(max_length=_TAG_MAX_ITEMS)] = []


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


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    today = date.today().isoformat()
    due_today = db.query(func.count(Flashcard.id)).filter(
        or_(Flashcard.next_review == None, Flashcard.next_review <= today)
    ).scalar() or 0
    total = db.query(func.count(Flashcard.id)).scalar() or 0

    reviewed_dates = {
        row[0] for row in
        db.query(Flashcard.last_reviewed).filter(Flashcard.last_reviewed.isnot(None)).all()
    }
    streak = 0
    check = date.today()
    while check.isoformat() in reviewed_dates:
        streak += 1
        check -= timedelta(days=1)

    return {"due_today": due_today, "total": total, "streak": streak}


@router.get("/review")
def get_cards_due_for_review(db: Session = Depends(get_db)):
    """
    Returns only flashcards due for review today or earlier.
    Used by the spaced repetition study mode.
    """
    today = date.today().isoformat()
    flashcards = db.query(Flashcard).filter(
        or_(Flashcard.next_review == None, Flashcard.next_review <= today)
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
def process_text(request: ProcessRequest):
    """
    Runs the full pipeline on plain text input.
    Returns the newly created flashcards.
    """
    try:
        final_state = run_pipeline(
            input_type="text",
            input_data=request.text,
            source=request.source,
            tags=request.tags
        )
    except Exception as e:
        print(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail="Pipeline failed. Check server logs.")

    saved_count = final_state["storage_result"]["saved"]
    return {
        "message": f"Successfully created {saved_count} flashcards",
        "saved": saved_count,
        "skipped": final_state["storage_result"]["skipped"],
        "flashcards": final_state["enrichment_result"]["flashcards"]
    }


@router.post("/translate")
def translate_text(request: TranslateTextRequest):
    """Instantly translates German text via DeepL. No pipeline involved."""
    try:
        translation = deepl_client.translate_sentence(request.text)
    except Exception as e:
        print(f"DeepL error: {e}")
        raise HTTPException(status_code=500, detail="Translation failed. Check server logs.")
    return {"translation": translation}


@router.post("/process/translation")
def process_translation(request: TranslationRequest):
    """
    Runs the pipeline on German text, using it as context for example sentences.
    Returns new flashcards created. Intended to be called alongside /translate.
    """
    try:
        final_state = run_pipeline(
            input_type="text",
            input_data=request.text,
            source="translator",
            tags=request.tags,
            context_de=request.text
        )
    except Exception as e:
        print(f"Pipeline error: {e}")
        raise HTTPException(status_code=500, detail="Pipeline failed. Check server logs.")

    saved_count = final_state["storage_result"]["saved"]
    return {
        "message": f"Successfully created {saved_count} flashcards",
        "saved": saved_count,
        "skipped": final_state["storage_result"]["skipped"],
        "flashcards": final_state["enrichment_result"].get("flashcards", [])
    }


@router.post("/process/image")
async def process_image(
    file: UploadFile = File(...),
    source: str = Form("image upload", max_length=200),
    tags: str = Form(""),
):
    """
    Accepts an image or PDF upload and runs the full pipeline.
    Automatically detects file type and routes accordingly.
    """
    safe_filename = Path(file.filename).name
    suffix = Path(safe_filename).suffix.lower()

    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="File type not allowed. Accepted: images (jpg, png, gif, bmp, webp) and PDF."
        )

    # Reject based on Content-Length before writing to disk when possible.
    # This avoids streaming a huge file all the way before rejecting it.
    content_length = file.size  # set by Starlette when available
    if content_length is not None and content_length > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

    temp_path = UPLOAD_FOLDER / f"{uuid.uuid4()}{suffix}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        actual_size = temp_path.stat().st_size
        if actual_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if actual_size > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="File too large. Maximum size is 10 MB.")

        input_type = "pdf" if suffix == ".pdf" else "image"

        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        try:
            final_state = run_pipeline(
                input_type=input_type,
                input_data=str(temp_path),
                source=source,
                tags=tags_list
            )
        except Exception as e:
            print(f"Pipeline error: {e}")
            raise HTTPException(status_code=500, detail="Pipeline failed. Check server logs.")

        saved_count = final_state["storage_result"]["saved"]
        return {
            "message": f"Successfully created {saved_count} flashcards",
            "saved": saved_count,
            "skipped": final_state["storage_result"]["skipped"],
        }

    finally:
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
        card.last_reviewed = date.today().isoformat()
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