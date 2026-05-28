import json
from pathlib import Path

from sqlalchemy.orm import Session

from backend.database.models import SeedWord

SEED_DIR = Path(__file__).parent.parent.parent / "seed_data"


def _seed_files():
    """Yield seed JSON files: subdirectory words.json files first, then legacy flat files."""
    seen = set()
    for f in sorted(SEED_DIR.glob("*/words.json")):
        seen.add(f)
        yield f
    for f in sorted(SEED_DIR.glob("*.json")):
        if f not in seen:
            yield f


def load_seeds(db: Session) -> None:
    """Populate seed_words from JSON files in seed_data/. Safe to call on every startup."""
    if not SEED_DIR.exists():
        return

    for json_file in _seed_files():
        data = json.loads(json_file.read_text(encoding="utf-8"))
        new_count = 0
        for item in data:
            if db.query(SeedWord).filter(SeedWord.id == item["id"]).first():
                continue
            db.add(SeedWord(
                id=item["id"],
                level=item["level"],
                lesson=item.get("lesson"),
                lesson_number=item.get("lesson_number"),
                german_word=item["german_word"],
                english_translation=item["english_translation"],
                word_class=item.get("word_class"),
                gender=item.get("gender"),
                plural_form=item.get("plural_form"),
                example_sentence_de=item.get("example_sentence_de"),
                example_sentence_en=item.get("example_sentence_en"),
                mnemonic=item.get("mnemonic"),
                gender_tip=item.get("gender_tip"),
            ))
            new_count += 1
        if new_count:
            db.commit()
            print(f"Loaded {new_count} seed words from {json_file.name}")
