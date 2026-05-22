# enrichment_agent.py
# Takes a raw list of German words from the parser agent and produces
# complete flashcard objects by combining DeepL translations and LLM enrichment.
# This agent orchestrates the tools — it does not call any APIs directly.

import uuid
from datetime import date

from pipeline.tools import deepl_client, llm_client


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
    tags: list[str] = None
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

    flashcards = []
    failures = []

    # Step 1 — Translate all words in one batch call to save API quota
    print(f"Translating {len(words)} words via DeepL...")
    translations = deepl_client.translate_batch(words)

    # Step 2 — Enrich each word individually with the LLM
    for word, translation in zip(words, translations):
        print(f"Enriching: {word}...")
        try:
            llm_data = llm_client.enrich_word(word)
            flashcard = _build_flashcard(
                german_word=word,
                english_translation=translation,
                llm_data=llm_data,
                source=source,
                tags=tags
            )
            flashcards.append(flashcard)

        except Exception as e:
            # If enrichment fails for one word we log it and continue.
            # We never let one bad word crash the entire batch.
            print(f"  Failed to enrich '{word}': {e}")
            failures.append({"word": word, "error": str(e)})

    print(f"Enrichment complete: {len(flashcards)} succeeded, {len(failures)} failed")
    return {"flashcards": flashcards, "failures": failures}