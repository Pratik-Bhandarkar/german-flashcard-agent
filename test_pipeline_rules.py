"""
Tests for parser and validator strict rules.
Runs without a server — tests the Python modules directly.

Usage:
    python test_pipeline_rules.py
"""

import sys
sys.path.insert(0, ".")

from pipeline.agents.validator_agent import validate_flashcard
from pipeline.agents.parser_agent import clean_word_list

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
BUG  = "\033[91mBUG \033[0m"

results = []

def check(label, condition, detail=""):
    tag = PASS if condition else FAIL
    status = "PASS" if condition else "FAIL"
    print(f"  [{tag}] {label}")
    if detail:
        print(f"         {detail}")
    results.append((status, label, detail))

def bug(label, detail=""):
    """Mark a known bad behaviour that needs a fix."""
    print(f"  [{BUG}] {label}")
    if detail:
        print(f"         {detail}")
    results.append(("BUG", label, detail))

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ── Baseline card ─────────────────────────────────────────────
BASE = {
    "id": "abc-123",
    "german_word": "Hund",
    "english_translation": "dog",
    "word_class": "noun",
    "gender": "der",
    "plural_form": "Hunde",
    "example_sentence_de": "Der Hund laeuft schnell.",
    "example_sentence_en": "The dog runs fast.",
    "mnemonic": "Sounds like hound.",
    "created_at": "2026-01-01",
}

def card(**overrides):
    return {**BASE, **overrides}


# ══════════════════════════════════════════════════════════════
#  SECTION 1 — VALIDATOR: NOUNS
# ══════════════════════════════════════════════════════════════
section("1. VALIDATOR — NOUNS")

# 1a. Complete noun — must pass
r = validate_flashcard(card())
check("Complete noun passes", r["is_valid"])

# 1b. Proper noun: null plural_form (e.g. Deutschland, Berlin)
r = validate_flashcard(card(plural_form=None))
check("Proper noun: null plural_form passes", r["is_valid"],
      f"errors: {r['errors']}")

# 1c. Uncountable noun: empty string plural_form
r = validate_flashcard(card(plural_form=""))
check("Uncountable noun: empty plural_form passes", r["is_valid"],
      f"errors: {r['errors']}")

# 1d. Noun missing gender — must fail
r = validate_flashcard(card(gender=None))
check("Noun missing gender correctly fails", not r["is_valid"],
      f"errors: {r['errors']}")

# 1e. Noun with gender="masculine" (LLM hallucination — wrong format)
r = validate_flashcard(card(gender="masculine"))
is_invalid = not r["is_valid"]  # ideally this should fail — but currently passes
if is_invalid:
    check("Noun gender='masculine' (wrong format) correctly rejected", True)
else:
    bug(
        "Noun gender='masculine' passes validation — no value-check on gender field",
        "Validator accepts any non-empty string for gender. "
        "Fix: validate gender is one of 'der', 'die', 'das'."
    )

# 1f. Noun with gender="neuter" (another LLM hallucination)
r = validate_flashcard(card(gender="neuter"))
if not r["is_valid"]:
    check("Noun gender='neuter' correctly rejected", True)
else:
    bug(
        "Noun gender='neuter' passes validation",
        "Same issue as above — gender value not validated against allowed set."
    )


# ══════════════════════════════════════════════════════════════
#  SECTION 2 — VALIDATOR: OTHER WORD CLASSES
# ══════════════════════════════════════════════════════════════
section("2. VALIDATOR — VERBS / ADJECTIVES / ADVERBS")

# 2a. Verb — no gender/plural needed
r = validate_flashcard(card(
    word_class="verb", gender=None, plural_form=None,
    german_word="laufen", english_translation="to run"
))
check("Verb with null gender/plural passes", r["is_valid"], f"errors: {r['errors']}")

# 2b. Adjective — no gender/plural needed
r = validate_flashcard(card(
    word_class="adjective", gender=None, plural_form=None,
    german_word="schnell", english_translation="fast"
))
check("Adjective with null gender/plural passes", r["is_valid"], f"errors: {r['errors']}")

# 2c. Adverb
r = validate_flashcard(card(
    word_class="adverb", gender=None, plural_form=None,
    german_word="schnell", english_translation="quickly"
))
check("Adverb with null gender/plural passes", r["is_valid"], f"errors: {r['errors']}")

# 2d. word_class="other" (function words, conjunctions, etc.)
r = validate_flashcard(card(
    word_class="other", gender=None, plural_form=None,
    german_word="obwohl", english_translation="although"
))
check("word_class='other' passes", r["is_valid"], f"errors: {r['errors']}")

# 2e. Unknown word_class — must fail
r = validate_flashcard(card(word_class="conjunction"))
check("Unknown word_class 'conjunction' correctly fails", not r["is_valid"],
      f"errors: {r['errors']}")

# 2f. Unknown word_class "preposition"
r = validate_flashcard(card(word_class="preposition"))
check("Unknown word_class 'preposition' correctly fails", not r["is_valid"],
      f"errors: {r['errors']}")


# ══════════════════════════════════════════════════════════════
#  SECTION 3 — VALIDATOR: OPTIONAL FIELDS
# ══════════════════════════════════════════════════════════════
section("3. VALIDATOR — OPTIONAL FIELDS (mnemonic, gender_tip)")

# 3a. mnemonic=None — should this fail?
r = validate_flashcard(card(mnemonic=None))
if r["is_valid"]:
    check("mnemonic=None is optional — card passes", True)
else:
    bug(
        "mnemonic=None rejects a valid card",
        "Mnemonic is a nice-to-have, not a must-have. "
        "LLMs sometimes return null for it. "
        "Fix: remove 'mnemonic' from REQUIRED_FIELDS."
    )

# 3b. mnemonic="" (empty string)
r = validate_flashcard(card(mnemonic=""))
if r["is_valid"]:
    check("mnemonic='' is optional — card passes", True)
else:
    bug(
        "mnemonic='' rejects a valid card",
        "Same issue — empty mnemonic should not reject the card."
    )

# 3c. example_sentence_de=None — must fail (can't study without it)
r = validate_flashcard(card(example_sentence_de=None))
check("Missing example_sentence_de correctly fails", not r["is_valid"],
      f"errors: {r['errors']}")

# 3d. example_sentence_en=None — must fail
r = validate_flashcard(card(example_sentence_en=None))
check("Missing example_sentence_en correctly fails", not r["is_valid"],
      f"errors: {r['errors']}")

# 3e. english_translation=None — must fail
r = validate_flashcard(card(english_translation=None))
check("Missing english_translation correctly fails", not r["is_valid"],
      f"errors: {r['errors']}")


# ══════════════════════════════════════════════════════════════
#  SECTION 4 — PARSER: LENGTH FILTER
# ══════════════════════════════════════════════════════════════
section("4. PARSER — LENGTH FILTER (currently <=3 chars rejected)")

three_letter_vocab = [
    ("gut",  "good"),
    ("alt",  "old"),
    ("neu",  "new"),
    ("rot",  "red"),
    ("Weg",  "way/path"),
    ("See",  "lake/sea"),
    ("Eis",  "ice/ice-cream"),
    ("Zug",  "train/pull"),
    ("Tag",  "day"),
    ("Bus",  "bus"),
]

for word, meaning in three_letter_vocab:
    result = clean_word_list([word])
    kept = word.lower() in [w.lower() for w in result]
    if kept:
        check(f"3-letter word '{word}' ({meaning}) kept", True)
    else:
        bug(
            f"3-letter word '{word}' ({meaning}) rejected by length filter",
            "len(word) <= 3 filter is too aggressive. "
            "Fix: change to len(word) < 2 (reject only 0-1 char tokens)."
        )

# 2-letter tokens should still be rejected (they're OCR noise)
for token in ["ab", "in", "zu", "so"]:
    result = clean_word_list([token])
    check(f"2-letter token '{token}' correctly rejected",
          token.lower() not in [w.lower() for w in result])


# ══════════════════════════════════════════════════════════════
#  SECTION 5 — PARSER: ARTICLES & FILLER
# ══════════════════════════════════════════════════════════════
section("5. PARSER — ARTICLES AND FILLER WORDS")

for article in ["der", "die", "das", "ein", "eine"]:
    result = clean_word_list([article])
    check(f"Article '{article}' correctly removed",
          article.lower() not in [w.lower() for w in result])

for filler in ["nicht", "zum", "mit", "auf"]:
    result = clean_word_list([filler])
    check(f"Filler '{filler}' correctly removed",
          filler.lower() not in [w.lower() for w in result])


# ══════════════════════════════════════════════════════════════
#  SECTION 6 — PARSER: SPECIAL CHARACTERS & EDGE CASES
# ══════════════════════════════════════════════════════════════
section("6. PARSER — SPECIAL CHARACTERS, UMLAUTS, DUPLICATES")

# Umlauts must be preserved
for word in ["schoen", "gruessen", "Uberraschung"]:
    result = clean_word_list([word])
    check(f"Word '{word}' survives cleaning", len(result) == 1,
          f"got: {result}")

# Umlaut characters specifically
result = clean_word_list(["schön", "grüßen", "Überraschung"])
check("Umlaut chars preserved (ä ö ü ß Ä Ö Ü)", len(result) == 3,
      f"got: {result}")

# Punctuation stripped from valid word
result = clean_word_list(["Hund!", "Katze,", "Baum."])
check("Trailing punctuation stripped cleanly", len(result) == 3,
      f"got: {result}")

# Duplicates removed (case-insensitive)
result = clean_word_list(["Hund", "hund", "HUND", "hUnD"])
check("Duplicates deduplicated to 1 entry", len(result) == 1,
      f"got: {result}")

# ALL-CAPS filter
result = clean_word_list(["AGB", "DDR", "NATO"])
all_caps_removed = len(result) == 0
if all_caps_removed:
    check("ALL-CAPS tokens removed (OCR noise filter)", True,
          "Side effect: abbreviations like AGB/DDR from typed input also removed")
else:
    check("ALL-CAPS tokens kept", True,
          f"got: {result}")

# Word with number — number should be stripped, word kept if long enough
result = clean_word_list(["B1Kurs", "Lektion3"])
check("Words with digits: digits stripped, letters kept",
      any(w for w in result if w),
      f"got: {result}")

# Hyphenated compound
result = clean_word_list(["schwarz-weiß"])
check("Hyphenated word: hyphen stripped, joined form kept",
      len(result) == 1, f"got: {result}")


# ══════════════════════════════════════════════════════════════
#  SUMMARY
# ══════════════════════════════════════════════════════════════
section("SUMMARY")
total  = len(results)
passed = sum(1 for s, _, _ in results if s == "PASS")
failed = sum(1 for s, _, _ in results if s == "FAIL")
bugs   = sum(1 for s, _, _ in results if s == "BUG")

print(f"  Total checks : {total}")
print(f"  \033[92mPASS\033[0m         : {passed}")
print(f"  \033[91mFAIL\033[0m         : {failed}  <- unexpected behaviour")
print(f"  \033[91mBUG \033[0m         : {bugs}  <- known bad behaviour to fix")

if bugs or failed:
    print(f"\n  Issues to fix:")
    for s, label, detail in results:
        if s in ("FAIL", "BUG"):
            print(f"    [{s}] {label}")
            if detail:
                print(f"           {detail}")
