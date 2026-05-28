# validator_agent.py
# Quality gate for flashcard objects produced by the enrichment agent.
# Checks every flashcard for completeness and correctness before storage.
# Never modifies flashcard content — only approves or rejects.

# Fields that every flashcard must have regardless of word class.
# mnemonic is intentionally excluded — it's optional. The LLM sometimes
# returns null for proper nouns or common words where no hook is needed.
REQUIRED_FIELDS = [
    "id",
    "german_word",
    "english_translation",
    "word_class",
    "example_sentence_de",
    "example_sentence_en",
    "created_at"
]

# Gender is required for nouns; plural_form is optional because proper nouns
# and uncountable nouns have no plural form.
NOUN_REQUIRED_FIELDS = [
    "gender",
]

# The only word classes we accept — anything else is an LLM hallucination
VALID_WORD_CLASSES = [
    "noun",
    "verb",
    "adjective",
    "adverb",
    "other"
]

# The only accepted article forms for German nouns
VALID_GENDERS = {"der", "die", "das"}


def _check_required_fields(flashcard: dict) -> list[str]:
    """
    Checks that all required fields are present and non-empty.

    Returns:
        List of error messages — empty list means no errors
    """
    errors = []

    for field in REQUIRED_FIELDS:
        # Check the field exists and is not None or empty string
        value = flashcard.get(field)
        if not value:
            errors.append(f"Missing required field: '{field}'")

    return errors


def _check_word_class(flashcard: dict) -> list[str]:
    """
    Checks that word_class is one of our accepted values.

    Returns:
        List of error messages — empty list means no errors
    """
    errors = []

    word_class = flashcard.get("word_class")
    if word_class and word_class not in VALID_WORD_CLASSES:
        errors.append(
            f"Invalid word_class: '{word_class}'. "
            f"Must be one of {VALID_WORD_CLASSES}"
        )

    return errors


def _check_noun_fields(flashcard: dict) -> list[str]:
    """
    If the word is a noun, checks that gender is present and a valid article.
    Non-nouns are allowed to have null gender and plural_form.

    Returns:
        List of error messages — empty list means no errors
    """
    errors = []

    if flashcard.get("word_class") == "noun":
        gender = flashcard.get("gender")
        if not gender:
            errors.append("Noun is missing required field: 'gender'")
        elif gender not in VALID_GENDERS:
            errors.append(
                f"Noun has invalid gender: '{gender}'. "
                f"Must be one of {sorted(VALID_GENDERS)}"
            )

    return errors


def validate_flashcard(flashcard: dict) -> dict:
    """
    Runs all validation checks on a single flashcard.

    Args:
        flashcard: flashcard dictionary from the enrichment agent

    Returns:
        Dictionary with:
        - "is_valid": True if all checks passed
        - "errors": list of error messages (empty if valid)
        - "flashcard": the original flashcard unchanged
    """
    errors = []

    # Run all three checks and collect any errors
    errors.extend(_check_required_fields(flashcard))
    errors.extend(_check_word_class(flashcard))
    errors.extend(_check_noun_fields(flashcard))

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "flashcard": flashcard
    }


def run(enrichment_result: dict) -> dict:
    """
    Main entry point for the Validator Agent.
    Validates every flashcard from the enrichment agent output.

    Args:
        enrichment_result: the dictionary returned by enrichment_agent.run()
                          contains "flashcards" and "failures" keys

    Returns:
        Dictionary with:
        - "valid": list of flashcards that passed all checks
        - "invalid": list of dicts with flashcard + error details
        - "enrichment_failures": failures carried over from enrichment agent
    """
    valid = []
    invalid = []

    for flashcard in enrichment_result["flashcards"]:
        result = validate_flashcard(flashcard)

        if result["is_valid"]:
            valid.append(flashcard)
        else:
            # Keep the flashcard alongside its errors for debugging
            invalid.append({
                "flashcard": flashcard,
                "errors": result["errors"]
            })
            print(f"  Invalid card '{flashcard.get('german_word')}': "
                  f"{result['errors']}")

    print(f"Validation complete: {len(valid)} valid, {len(invalid)} invalid")

    return {
        "valid": valid,
        "invalid": invalid,
        # Carry enrichment failures forward so nothing gets lost
        "enrichment_failures": enrichment_result["failures"]
    }