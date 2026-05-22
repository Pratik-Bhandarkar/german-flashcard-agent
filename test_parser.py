# test_parser.py
# Quick manual test for the parser agent.
# Tests all three input types: text, image, and PDF.
# Run this from the project root: python test_parser.py

from pipeline.agents import parser_agent

# --- Test 1: Plain text input ---
print("=== Test 1: Plain Text ===")
sample_text = "Hund, Katze, Bahnhof, laufen, schlafen"
result = parser_agent.run(input_type="text", input_data=sample_text)
print(f"Input:  {sample_text}")
print(f"Output: {result}")
print()

# --- Test 2: Wrong input type ---
print("=== Test 2: Invalid Input Type ===")
try:
    parser_agent.run(input_type="video", input_data="something")
except ValueError as e:
    print(f"Caught expected error: {e}")
print()

print("=== All tests done ===")

# --- Test 3: DeepL single word translation ---
print("=== Test 3: Single Word Translation ===")
from pipeline.tools import deepl_client

single = deepl_client.translate_to_english("Hund")
print(f"Input:  Hund")
print(f"Output: {single}")
print()

# --- Test 4: DeepL batch translation ---
print("=== Test 4: Batch Translation ===")
words = ["Hund", "Katze", "Bahnhof", "laufen", "schlafen"]
translations = deepl_client.translate_batch(words)

for german, english in zip(words, translations):
    print(f"  {german} → {english}")
print()

# --- Test 5: LLM enrichment with local Ollama ---
print("=== Test 5: LLM Word Enrichment ===")
from pipeline.tools import llm_client

test_words = ["Hund", "laufen", "schön"]

for word in test_words:
    print(f"\nEnriching: {word}")
    result = llm_client.enrich_word(word)
    for key, value in result.items():
        print(f"  {key}: {value}")

# --- Test 6: Enrichment Agent ---
print("=== Test 6: Enrichment Agent ===")
from pipeline.agents import enrichment_agent

words = ["Hund", "laufen", "schön"]
result = enrichment_agent.run(
    words=words,
    source="test run",
    tags=["test", "B1"]
)

print(f"\nSuccessfully enriched: {len(result['flashcards'])} cards")
print(f"Failed: {len(result['failures'])} words")

print("\n--- Flashcards ---")
for card in result["flashcards"]:
    print(f"\n  Word:       {card['german_word']}")
    print(f"  Translation:{card['english_translation']}")
    print(f"  Class:      {card['word_class']}")
    print(f"  Gender:     {card['gender']}")
    print(f"  Plural:     {card['plural_form']}")
    print(f"  Sentence:   {card['example_sentence_de']}")
    print(f"  Mnemonic:   {card['mnemonic']}")
    print(f"  Tags:       {card['tags']}")
    print(f"  ID:         {card['id']}")
    print(f"  Created:    {card['created_at']}")

    # --- Test 7: Validator Agent ---
print("=== Test 7: Validator Agent ===")
from pipeline.agents import validator_agent

# Test 7a: Valid flashcards from enrichment agent
print("\n-- Test 7a: Valid flashcards --")
validation_result = validator_agent.run(result)

print(f"Valid cards:   {len(validation_result['valid'])}")
print(f"Invalid cards: {len(validation_result['invalid'])}")
print(f"Enrich failures: {len(validation_result['enrichment_failures'])}")

# Test 7b: Deliberately broken flashcard
print("\n-- Test 7b: Deliberately broken flashcard --")
broken_flashcard = {
    "id": "test-123",
    "german_word": "Hund",
    "english_translation": "dog",
    "word_class": "noun",
    # deliberately missing gender, plural_form, sentences, mnemonic
    "created_at": "2026-05-22"
}

broken_result = validator_agent.validate_flashcard(broken_flashcard)
print(f"Is valid: {broken_result['is_valid']}")
print(f"Errors found:")
for error in broken_result["errors"]:
    print(f"  - {error}")

# --- Test 8: Storage Agent ---
print("=== Test 8: Storage Agent ===")
from pipeline.agents import storage_agent

# Save the validated flashcards from Test 7
print("\n-- Test 8a: Saving valid flashcards --")
storage_result = storage_agent.run(validation_result)

print(f"\nSaved:   {storage_result['saved']}")
print(f"Skipped: {storage_result['skipped']}")
print(f"Failures: {len(storage_result['failures'])}")

# Read them back from the database to confirm they were saved
print("\n-- Test 8b: Reading back from database --")
all_cards = storage_agent.get_all_flashcards()
print(f"Total cards in database: {len(all_cards)}")

for card in all_cards:
    print(f"\n  Word:    {card['german_word']}")
    print(f"  Gender:  {card['gender']}")
    print(f"  Tags:    {card['tags']}")
    print(f"  Created: {card['created_at']}")