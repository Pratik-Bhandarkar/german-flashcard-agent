# storage_agent.py
# Responsible for persisting validated flashcards to the database.
# Uses SQLAlchemy models instead of raw SQL for type safety and consistency.
# This is the final agent in the pipeline — it only receives valid flashcards.

from sqlalchemy.orm import Session

from backend.database.db import SessionLocal
from backend.database.models import Flashcard


def _save_flashcard(db: Session, flashcard: dict) -> bool:
    """
    Inserts a single flashcard into the database.
    Returns True if saved, False if already exists.
    """
    existing = db.query(Flashcard).filter(
        Flashcard.german_word == flashcard["german_word"]
    ).first()

    if existing:
        print(f"  Skipped (already exists): {flashcard['german_word']}")
        return False

    # Create a SQLAlchemy model instance from the dictionary
    db_flashcard = Flashcard(
        id=flashcard["id"],
        german_word=flashcard["german_word"],
        english_translation=flashcard["english_translation"],
        word_class=flashcard.get("word_class"),
        gender=flashcard.get("gender"),
        plural_form=flashcard.get("plural_form"),
        example_sentence_de=flashcard.get("example_sentence_de"),
        example_sentence_en=flashcard.get("example_sentence_en"),
        mnemonic=flashcard.get("mnemonic"),
        gender_tip=flashcard.get("gender_tip"),
        source=flashcard.get("source"),
        tags=flashcard.get("tags", []),
        difficulty=flashcard.get("difficulty"),
        next_review=flashcard.get("next_review"),
        created_at=flashcard["created_at"]
    )

    db.add(db_flashcard)
    return True


def run(validation_result: dict) -> dict:
    """
    Main entry point for the Storage Agent.
    Saves all valid flashcards to the database.

    Args:
        validation_result: dictionary returned by validator_agent.run()
                          contains "valid", "invalid", "enrichment_failures"

    Returns:
        Dictionary with:
        - "saved": count of successfully saved flashcards
        - "skipped": count of invalid cards not saved
        - "failures": combined list of all failures for logging
    """
    valid_flashcards = validation_result["valid"]

    db = SessionLocal()
    saved_count = 0

    try:
        for flashcard in valid_flashcards:
            try:
                if _save_flashcard(db, flashcard):
                    saved_count += 1
                    print(f"  Saved: {flashcard['german_word']}")
            except Exception as e:
                print(f"  Failed to save '{flashcard['german_word']}': {e}")

        # Commit all inserts in one go
        db.commit()

    except Exception as e:
        # If anything goes wrong roll back all inserts
        # so we never end up with partial data in the database
        db.rollback()
        raise e

    finally:
        db.close()

    skipped_count = len(validation_result["invalid"])
    all_failures = (
        validation_result["invalid"] +
        validation_result["enrichment_failures"]
    )

    print(f"Storage complete: {saved_count} saved, {skipped_count} skipped")

    return {
        "saved": saved_count,
        "skipped": skipped_count,
        "failures": all_failures
    }