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