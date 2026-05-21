# llm_client.py
# A clean wrapper around our LLM of choice — either Ollama (local) or OpenAI.
# Responsible for one thing: given a German word, return structured enrichment data.
# The enrichment agent calls this instead of touching LLM APIs directly.

import json
import requests
from openai import OpenAI

from pipeline.config import (
    USE_LOCAL_LLM,
    OLLAMA_MODEL,
    OLLAMA_BASE_URL,
    OPENAI_API_KEY,
    OPENAI_MODEL
)


# Initialise OpenAI client once at module level.
# This is only used when USE_LOCAL_LLM is False.
openai_client = OpenAI(api_key=OPENAI_API_KEY)


# This is the instruction we send to the LLM for every word.
# It is defined here as a constant so it is easy to find and improve.
ENRICHMENT_PROMPT_TEMPLATE = """
You are a German language expert. Given a German word, return a JSON object with the following fields:

- word_class: one of "noun", "verb", "adjective", "adverb", "other"
- gender: "der", "die", "das", or null if not a noun
- plural_form: the plural form of the word, or null if not a noun
- example_sentence_de: a simple, natural German sentence using the word
- example_sentence_en: the English translation of that sentence
- mnemonic: a creative memory hook in English to help an English speaker remember the German word, the memory hook shouldn't be too long, ideally just one sentence or phrase.

Return ONLY the JSON object. No explanation, no markdown, no extra text.

German word: {word}
"""


def _parse_llm_response(raw_response: str) -> dict:
    """
    Safely parses the LLM's raw text response into a Python dictionary.
    LLMs sometimes return malformed JSON — we handle the most common cases:
    - Markdown code fences around the JSON
    - Special characters like umlauts causing encoding issues
    - Extra text before or after the JSON object
    """
    cleaned = raw_response.strip()

    # Remove markdown code fences if present (```json ... ``` or ``` ... ```)
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
        cleaned = cleaned.rsplit("```", 1)[0]

    # Sometimes the LLM adds text before or after the JSON object.
    # We find the first { and last } and extract just that part.
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"No valid JSON object found in LLM response: {cleaned}")

    cleaned = cleaned[start:end + 1]

    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned malformed JSON: {e}\nRaw response: {cleaned}")


def _enrich_with_ollama(word: str) -> dict:
    """
    Sends an enrichment request to the local Ollama instance.

    Args:
        word: German word to enrich

    Returns:
        Dictionary of enrichment data
    """
    prompt = ENRICHMENT_PROMPT_TEMPLATE.format(word=word)

    # Ollama exposes a simple HTTP API — we call it directly with requests
    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            # stream=False means we wait for the full response
            # instead of receiving it word by word
            "stream": False
        }
    )

    raw_text = response.json()["response"]
    return _parse_llm_response(raw_text)


def _enrich_with_openai(word: str) -> dict:
    """
    Sends an enrichment request to the OpenAI API.

    Args:
        word: German word to enrich

    Returns:
        Dictionary of enrichment data
    """
    prompt = ENRICHMENT_PROMPT_TEMPLATE.format(word=word)

    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            # System message sets the behaviour of the model
            {"role": "system", "content": "You are a German language expert."},
            {"role": "user", "content": prompt}
        ]
    )

    raw_text = response.choices[0].message.content
    return _parse_llm_response(raw_text)


def enrich_word(word: str) -> dict:
    """
    Main entry point for the LLM client.
    Routes to Ollama or OpenAI based on the USE_LOCAL_LLM config flag.

    Args:
        word: German word to enrich

    Returns:
        Dictionary containing word_class, gender, plural_form,
        example_sentence_de, example_sentence_en, and mnemonic
    """
    if USE_LOCAL_LLM:
        return _enrich_with_ollama(word)
    else:
        return _enrich_with_openai(word)