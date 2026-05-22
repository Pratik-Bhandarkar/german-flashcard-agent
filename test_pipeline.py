# test_pipeline.py
# End to end test of the full LangGraph flashcard generation pipeline.
# Run this from the project root: python test_pipeline.py

from pipeline.graph import run_pipeline

# --- Test: Full pipeline with plain text input ---
final_state = run_pipeline(
    input_type="text",
    input_data="Krankenhaus, trinken, kalt, die Straße, lesen",
    source="manual test run",
    tags=["test", "mixed"]
)

# Print a summary of every saved flashcard
print("\n--- Saved Flashcards ---")
for card in final_state["enrichment_result"]["flashcards"]:
    print(f"\n  {card['german_word']} → {card['english_translation']}")
    print(f"  Class:    {card['word_class']}")
    print(f"  Gender:   {card['gender']}")
    print(f"  Sentence: {card['example_sentence_de']}")
    print(f"  Mnemonic: {card['mnemonic']}")