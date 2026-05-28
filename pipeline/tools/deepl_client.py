# deepl_client.py
# A clean wrapper around the DeepL API.
# Responsible for one thing only — translating German text to English.
# The enrichment agent calls this instead of touching the DeepL API directly.

import deepl

from pipeline.config import DEEPL_API_KEY, DEEPL_TARGET_LANG


# Initialise the DeepL translator once at module level.
# We do this here so every call reuses the same connection
# instead of creating a new one each time.
translator = deepl.Translator(DEEPL_API_KEY)


def translate_sentence(text: str) -> str:
    """
    Translates a full German sentence or paragraph to English.

    Args:
        text: German text to translate

    Returns:
        English translation as a single string
    """
    result = translator.translate_text(
        text,
        source_lang="DE",
        target_lang=DEEPL_TARGET_LANG
    )
    return result.text


def translate_batch(german_words: list[str]) -> list[str]:
    """
    Translates a list of German words to English in a single API call.
    Always prefer this over calling translate_to_english in a loop —
    one batch call is faster and uses less of your API quota.

    Args:
        german_words: list of German words

    Returns:
        List of English translations in the same order as input
    """
    results = translator.translate_text(
        german_words,
        source_lang="DE",
        target_lang=DEEPL_TARGET_LANG
    )

    # Each item in results has a .text attribute with the translation
    return [result.text for result in results]