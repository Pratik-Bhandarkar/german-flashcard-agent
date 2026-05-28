"""
Generates a pre-enriched seed JSON file from a plain word list.

Usage:
    python generate_seed_data.py --input seed_data/B1/input.txt --level B1

Input file format (one entry per line):
    Wohnung
    umziehen
    Lesson 2          <- lines starting with "Lesson" mark the start of a new lesson
    Stelle
    ...

Or CSV format:
    german_word,lesson_number,lesson_name
    Wohnung,1,Alltag und Wohnen
    umziehen,1,Alltag und Wohnen

Each word is passed through the pipeline's enrichment agent (DeepL + LLM).
Estimated time: ~3-5 seconds per word. For 800 words expect ~45-60 minutes.
Existing entries in the output file are skipped (safe to resume after interruption).
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, ".")

from pipeline.tools import deepl_client, llm_client
from pipeline.agents.enrichment_agent import _build_flashcard, _get_gender_tip


def _load_existing(output_path: Path) -> dict:
    if output_path.exists():
        data = json.loads(output_path.read_text(encoding="utf-8"))
        return {entry["german_word"]: entry for entry in data}
    return {}


def _save(output_path: Path, entries: list) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def _parse_word_list(input_path: Path):
    """
    Parses the input file into a list of (german_word, lesson_number, lesson_name) tuples.
    Supports plain word list (with "Lesson N" markers) and CSV.
    """
    lines = input_path.read_text(encoding="utf-8").splitlines()
    entries = []

    if input_path.suffix.lower() == ".csv":
        import csv, io
        reader = csv.DictReader(io.StringIO("\n".join(lines)))
        for row in reader:
            entries.append((
                row["german_word"].strip(),
                int(row.get("lesson_number", 1)),
                row.get("lesson_name", "Lesson 1").strip(),
            ))
        return entries

    current_lesson_num = 1
    current_lesson_name = "Lesson 1"
    _ARTICLES = {"der ", "die ", "das ", "Der ", "Die ", "Das "}

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("lesson"):
            parts = line.split("—", 1)
            try:
                current_lesson_num = int(parts[0].strip().split()[-1])
            except (ValueError, IndexError):
                current_lesson_num += 1
            current_lesson_name = line
            continue
        for art in _ARTICLES:
            if line.startswith(art):
                line = line[len(art):]
                break
        entries.append((line, current_lesson_num, current_lesson_name))

    return entries


def main():
    parser = argparse.ArgumentParser(description="Generate pre-enriched seed vocabulary JSON")
    parser.add_argument("--input",  required=True, help="Path to word list file (.txt or .csv)")
    parser.add_argument("--level",  default="B1",  help="Vocabulary level, e.g. B1")
    parser.add_argument("--output", default=None,  help="Output JSON path (default: seed_data/{LEVEL}/words.json)")
    parser.add_argument("--delay",  type=float, default=1.0, help="Seconds to wait between LLM calls")
    args = parser.parse_args()

    input_path  = Path(args.input)
    level       = args.level.upper()
    output_path = Path(args.output) if args.output else Path(f"seed_data/{level}/words.json")

    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    word_entries = _parse_word_list(input_path)
    existing     = _load_existing(output_path)
    results      = list(existing.values())
    skipped = done = failed = 0

    print(f"Found {len(word_entries)} words. {len(existing)} already enriched.")

    for i, (word, lesson_num, lesson_name) in enumerate(word_entries, 1):
        if word in existing:
            skipped += 1
            continue

        print(f"[{i}/{len(word_entries)}] Enriching: {word} ...")
        try:
            translation = deepl_client.translate_batch([word])[0]
            llm_data    = llm_client.enrich_word(word)

            if not llm_data.get("is_valid", True):
                print(f"  Skipped (LLM marked invalid): {word}")
                failed += 1
                continue

            entry = {
                "id":                   f"{level.lower()}_{len(results) + 1:03d}",
                "level":                level,
                "lesson":               lesson_name,
                "lesson_number":        lesson_num,
                "german_word":          word,
                "english_translation":  translation,
                "word_class":           llm_data.get("word_class"),
                "gender":               llm_data.get("gender"),
                "plural_form":          llm_data.get("plural_form"),
                "example_sentence_de":  llm_data.get("example_sentence_de"),
                "example_sentence_en":  llm_data.get("example_sentence_en"),
                "mnemonic":             llm_data.get("mnemonic"),
                "gender_tip":           _get_gender_tip(word, llm_data.get("gender")),
            }
            results.append(entry)
            existing[word] = entry
            done += 1

            _save(output_path, results)

            if args.delay > 0:
                time.sleep(args.delay)

        except Exception as e:
            print(f"  ERROR enriching '{word}': {e}")
            failed += 1

    print(f"\nDone. Added: {done}  Skipped: {skipped}  Failed: {failed}")
    print(f"Output: {output_path} ({len(results)} total entries)")


if __name__ == "__main__":
    main()
