# enrichment_agent.py
# Takes a raw list of German words from the parser agent and produces
# complete flashcard objects by combining DeepL translations and LLM enrichment.
# This agent orchestrates the tools — it does not call any APIs directly.

import uuid
from datetime import date

from pipeline.tools import deepl_client, llm_client
from backend.database.db import SessionLocal
from backend.database.models import Flashcard


# Suffix → (expected gender, tip text). Longer suffixes listed first to avoid
# shorter ones matching prematurely (e.g. -tum before -um).
_GENDER_SUFFIX_RULES: list[tuple[str, str, str]] = [
    # Die — very reliable
    ("ung",    "die", "Words ending in -ung are always feminine"),
    ("heit",   "die", "Words ending in -heit are always feminine"),
    ("keit",   "die", "Words ending in -keit are always feminine"),
    ("schaft", "die", "Words ending in -schaft are always feminine"),
    ("ität",   "die", "Words ending in -ität are always feminine"),
    ("ion",    "die", "Words ending in -ion are always feminine"),
    ("tät",    "die", "Words ending in -tät are always feminine"),
    ("enz",    "die", "Words ending in -enz are usually feminine"),
    ("anz",    "die", "Words ending in -anz are usually feminine"),
    ("ik",     "die", "Words ending in -ik are usually feminine"),
    ("ie",     "die", "Words ending in -ie are usually feminine"),
    # Das — very reliable
    ("chen",   "das", "Diminutives ending in -chen are always neuter"),
    ("lein",   "das", "Diminutives ending in -lein are always neuter"),
    ("ment",   "das", "Words ending in -ment are usually neuter"),
    ("tum",    "das", "Words ending in -tum are usually neuter"),
    ("um",     "das", "Words ending in -um are usually neuter"),
    # Der — fairly reliable
    ("ling",   "der", "Words ending in -ling are masculine"),
    ("ismus",  "der", "Words ending in -ismus are masculine"),
    ("ist",    "der", "Words ending in -ist are usually masculine"),
    ("or",     "der", "Words ending in -or are usually masculine"),
    ("ig",     "der", "Words ending in -ig are usually masculine"),
    ("er",     "der", "Many words ending in -er are masculine"),
]


def _get_gender_tip(word: str, gender: str | None) -> str | None:
    """Returns a suffix-based article tip when the word matches a known pattern."""
    if not gender:
        return None
    word_lower = word.lower()
    for suffix, expected_gender, tip in _GENDER_SUFFIX_RULES:
        if word_lower.endswith(suffix) and gender == expected_gender:
            return tip
    return None


def _get_existing_words() -> set[str]:
    db = SessionLocal()
    try:
        rows = db.query(Flashcard.german_word).all()
        return {row[0].lower() for row in rows}
    finally:
        db.close()


def _build_flashcard(
    german_word: str,
    english_translation: str,
    llm_data: dict,
    source: str,
    tags: list[str]
) -> dict:
    """
    Combines all enrichment data into a single flashcard dictionary.
    This is the data model every downstream agent and the database expects.

    Args:
        german_word: the original German word
        english_translation: DeepL translation
        llm_data: enrichment data from the LLM
        source: where the word came from
        tags: user defined labels for filtering

    Returns:
        Complete flashcard dictionary
    """
    return {
        # Unique identifier for this flashcard — generated once at creation
        "id": str(uuid.uuid4()),

        "german_word": german_word,
        "english_translation": english_translation,

        # LLM enrichment fields
        "word_class": llm_data.get("word_class"),
        "gender": llm_data.get("gender"),
        "plural_form": llm_data.get("plural_form"),
        "example_sentence_de": llm_data.get("example_sentence_de"),
        "example_sentence_en": llm_data.get("example_sentence_en"),
        "mnemonic": llm_data.get("mnemonic"),
        "gender_tip": _get_gender_tip(german_word, llm_data.get("gender")),

        # Metadata
        "source": source,
        "tags": tags,

        # Spaced repetition fields — null until the user starts studying
        "difficulty": None,
        "next_review": None,

        # Timestamp — recorded as ISO format date string
        "created_at": date.today().isoformat()
    }


def run(
    words: list[str],
    source: str = "unknown",
    tags: list[str] = None,
    context_de: str = ""
) -> dict:
    """
    Main entry point for the Enrichment Agent.
    Takes a list of German words and returns enriched flashcard objects.

    Args:
        words: list of German words from the parser agent
        source: description of where the words came from
        tags: optional list of tags to apply to all cards in this batch

    Returns:
        Dictionary with:
        - "flashcards": list of successfully enriched flashcard dicts
        - "failures": list of words that failed enrichment with error info
    """
    # Default tags to empty list if none provided
    # We avoid using [] as a default argument — a common Python gotcha
    if tags is None:
        tags = []

    existing = _get_existing_words()
    new_words = [w for w in words if w.lower() not in existing]
    skipped_count = len(words) - len(new_words)
    if skipped_count:
        print(f"Skipped {skipped_count} word(s) already in DB — no API calls made")
    words = new_words

    flashcards = []
    failures = []

    if not words:
        return {"flashcards": [], "failures": []}

    # Step 1 — Translate all words in one batch call to save API quota
    print(f"Translating {len(words)} words via DeepL...")
    translations = deepl_client.translate_batch(words)

    # Step 2 — Enrich each word individually with the LLM
    for word, translation in zip(words, translations):
        print(f"Enriching: {word}...")
        try:
            llm_data = llm_client.enrich_word(word, context_de=context_de)

            # LLM flagged this as not a real German word — skip it
            if not llm_data.get("is_valid", True):
                print(f"  Skipped (not a valid word): {word}")
                continue

            flashcard = _build_flashcard(
                german_word=word,
                english_translation=translation,
                llm_data=llm_data,
                source=source,
                tags=tags
            )
            flashcards.append(flashcard)

        except Exception as e:
            print(f"  Failed to enrich '{word}': {e}")
            failures.append({"word": word, "error": str(e)})

    print(f"Enrichment complete: {len(flashcards)} succeeded, {len(failures)} failed")
    return {"flashcards": flashcards, "failures": failures}