# storage_agent.py
# Responsible for persisting validated flashcards to the SQLite database.
# This is the final agent in the pipeline — it only receives valid flashcards.

import sqlite3
import json

from pipeline.config import DATABASE_PATH


def _get_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    The database file is created automatically if it doesn't exist yet.
    """
    connection = sqlite3.connect(DATABASE_PATH)

    # Row factory makes rows behave like dictionaries
    # so we can access columns by name instead of index
    connection.row_factory = sqlite3.Row

    return connection


def _create_table_if_not_exists(connection: sqlite3.Connection) -> None:
    """
    Creates the flashcards table if it doesn't already exist.
    Safe to call every time — won't overwrite existing data.
    """
    connection.execute("""
        CREATE TABLE IF NOT EXISTS flashcards (
            id TEXT PRIMARY KEY,
            german_word TEXT NOT NULL,
            english_translation TEXT NOT NULL,
            word_class TEXT,
            gender TEXT,
            plural_form TEXT,
            example_sentence_de TEXT,
            example_sentence_en TEXT,
            mnemonic TEXT,
            source TEXT,
            tags TEXT,
            difficulty TEXT,
            next_review TEXT,
            created_at TEXT NOT NULL
        )
    """)
    connection.commit()


def _save_flashcard(connection: sqlite3.Connection, flashcard: dict) -> None:
    """
    Inserts a single flashcard into the database.
    Skips silently if a card with the same ID already exists.

    Args:
        connection: active database connection
        flashcard: validated flashcard dictionary
    """
    # Tags is a list in Python but SQLite only stores text.
    # We convert it to a JSON string for storage and back when reading.
    tags_as_string = json.dumps(flashcard.get("tags", []))

    # INSERT OR IGNORE means if a card with this ID already exists
    # we skip it instead of throwing an error
    connection.execute("""
        INSERT OR IGNORE INTO flashcards (
            id,
            german_word,
            english_translation,
            word_class,
            gender,
            plural_form,
            example_sentence_de,
            example_sentence_en,
            mnemonic,
            source,
            tags,
            difficulty,
            next_review,
            created_at
        ) VALUES (
            :id,
            :german_word,
            :english_translation,
            :word_class,
            :gender,
            :plural_form,
            :example_sentence_de,
            :example_sentence_en,
            :mnemonic,
            :source,
            :tags,
            :difficulty,
            :next_review,
            :created_at
        )
    """, {**flashcard, "tags": tags_as_string})


def get_all_flashcards() -> list[dict]:
    """
    Retrieves all flashcards from the database.
    Used later by the FastAPI backend to serve cards to the frontend.

    Returns:
        List of flashcard dictionaries
    """
    connection = _get_connection()
    _create_table_if_not_exists(connection)

    cursor = connection.execute(
        "SELECT * FROM flashcards ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    connection.close()

    flashcards = []
    for row in rows:
        card = dict(row)
        # Convert tags back from JSON string to Python list
        card["tags"] = json.loads(card["tags"]) if card["tags"] else []
        flashcards.append(card)

    return flashcards


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

    connection = _get_connection()

    # Ensure the table exists before we try to insert anything
    _create_table_if_not_exists(connection)

    saved_count = 0

    for flashcard in valid_flashcards:
        try:
            _save_flashcard(connection, flashcard)
            saved_count += 1
            print(f"  Saved: {flashcard['german_word']}")
        except Exception as e:
            print(f"  Failed to save '{flashcard['german_word']}': {e}")

    # Commit all inserts in one go — more efficient than committing one by one
    connection.commit()
    connection.close()

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