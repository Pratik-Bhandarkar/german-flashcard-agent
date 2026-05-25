# test_pipeline.py
# End to end test of the full LangGraph flashcard generation pipeline.
# Run this from the project root: python test_pipeline.py

from pipeline.graph import run_pipeline

# # --- Test: Full pipeline with plain text input ---
# final_state = run_pipeline(
#     input_type="text",
#     input_data="Krankenhaus, trinken, kalt, die Straße, lesen",
#     source="manual test run",
#     tags=["test", "mixed"]
# )

# # Print a summary of every saved flashcard
# print("\n--- Saved Flashcards ---")
# for card in final_state["enrichment_result"]["flashcards"]:
#     print(f"\n  {card['german_word']} → {card['english_translation']}")
#     print(f"  Class:    {card['word_class']}")
#     print(f"  Gender:   {card['gender']}")
#     print(f"  Sentence: {card['example_sentence_de']}")
#     print(f"  Mnemonic: {card['mnemonic']}")

# # --- Test: Real image input ---
# print("\n" + "=" * 50)
# print("Testing real image input")
# print("=" * 50)

# from pipeline.agents import parser_agent

# words = parser_agent.run(
#     input_type="image",
#     input_data="test_inputs/lesson9.png"
# )

# print(f"\nExtracted {len(words)} words:")
# for word in words:
#     print(f"  {word}")

# --- Test: Pipeline with sample of real image words ---
print("\n" + "=" * 50)
print("Testing pipeline with real vocab sample")
print("=" * 50)

sample_words = [
    "Kunstwerk", "musizieren", "traditionell",
    "beson", "einhundertzwölf", "Broschüre"
]

from pipeline.agents import enrichment_agent
sample_result = enrichment_agent.run(
    words=sample_words,
    source="lesson9 sample",
    tags=["Lektion9", "Kunst"]
)

print(f"\nValid flashcards: {len(sample_result['flashcards'])}")
print(f"Skipped invalid:  {len(sample_result['failures'])}")
for card in sample_result["flashcards"]:
    print(f"\n  {card['german_word']} → {card['english_translation']}")
    print(f"  Class: {card['word_class']}")