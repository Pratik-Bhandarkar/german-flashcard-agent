import hashlib
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.models import Flashcard, SeedWord

router = APIRouter(prefix="/library", tags=["library"])

_CEFR_LEVELS = [
    {"level": "A1", "label": "Beginner",           "locked": True},
    {"level": "A2", "label": "Elementary",          "locked": True},
    {"level": "B1", "label": "Intermediate",        "locked": False},
    {"level": "B2", "label": "Upper-Intermediate",  "locked": True},
    {"level": "C1", "label": "Advanced",            "locked": True},
    {"level": "C2", "label": "Mastery",             "locked": True},
]


class ActivateLessonRequest(BaseModel):
    lesson_number: int


class BulkActivateRequest(BaseModel):
    word_ids: list[str]


@router.get("/words-of-day")
def get_words_of_day(db: Session = Depends(get_db)):
    activated_ids = {
        row[0] for row in
        db.query(Flashcard.seeded_from).filter(Flashcard.seeded_from.isnot(None)).all()
    }
    all_words = db.query(SeedWord).filter(SeedWord.level == "B1").all()
    pool = sorted([w for w in all_words if w.id not in activated_ids], key=lambda w: w.id)
    if not pool:
        pool = sorted(all_words, key=lambda w: w.id)
    if len(pool) <= 3:
        return [w.to_dict() for w in pool]

    day_hash = int(hashlib.md5(date.today().isoformat().encode()).hexdigest(), 16)
    n = len(pool)
    selected, seen, i = [], set(), 0
    while len(selected) < 3:
        idx = (day_hash + i * 1_000_003) % n
        if idx not in seen:
            seen.add(idx)
            selected.append(pool[idx])
        i += 1
    return [w.to_dict() for w in selected]


@router.get("/levels")
def get_levels(db: Session = Depends(get_db)):
    result = []
    for meta in _CEFR_LEVELS:
        lvl = meta["level"]
        total = db.query(func.count(SeedWord.id)).filter(SeedWord.level == lvl).scalar() or 0
        activated = 0
        if total:
            activated = (
                db.query(func.count(Flashcard.id))
                .filter(
                    Flashcard.seeded_from.in_(
                        db.query(SeedWord.id).filter(SeedWord.level == lvl)
                    )
                )
                .scalar() or 0
            )
        result.append({**meta, "total_words": total, "activated_words": activated})
    return result


@router.get("/{level}/words")
def get_words(
    level: str,
    lesson: int | None = None,
    word_class: str | None = None,
    db: Session = Depends(get_db),
):
    level_upper = level.upper()
    query = db.query(SeedWord).filter(SeedWord.level == level_upper)
    if lesson is not None:
        query = query.filter(SeedWord.lesson_number == lesson)
    if word_class:
        query = query.filter(SeedWord.word_class == word_class)
    seeds = query.order_by(SeedWord.lesson_number, SeedWord.id).all()

    activated_ids = {
        row[0]
        for row in db.query(Flashcard.seeded_from)
        .filter(Flashcard.seeded_from.isnot(None))
        .all()
    }

    total = db.query(func.count(SeedWord.id)).filter(SeedWord.level == level_upper).scalar() or 0
    activated_total = len(activated_ids & {s.id for s in db.query(SeedWord).filter(SeedWord.level == level_upper).all()})

    meta = next((m for m in _CEFR_LEVELS if m["level"] == level_upper), None)
    if meta is None:
        raise HTTPException(status_code=404, detail="Level not found")

    return {
        "level": level_upper,
        "label": meta["label"],
        "total_words": total,
        "activated_words": activated_total,
        "words": [{**w.to_dict(), "activated": w.id in activated_ids} for w in seeds],
    }


@router.post("/{level}/{word_id}/activate")
def activate_word(level: str, word_id: str, db: Session = Depends(get_db)):
    seed = db.query(SeedWord).filter(
        SeedWord.id == word_id,
        SeedWord.level == level.upper(),
    ).first()
    if not seed:
        raise HTTPException(status_code=404, detail="Seed word not found")

    if db.query(Flashcard).filter(Flashcard.seeded_from == word_id).first():
        raise HTTPException(status_code=409, detail="Word already in your deck")

    existing = db.query(Flashcard).filter(Flashcard.german_word == seed.german_word).first()
    if existing:
        existing.seeded_from = word_id
        db.commit()
        return {**existing.to_dict(), "activated": True}

    card = Flashcard(
        id=str(uuid.uuid4()),
        german_word=seed.german_word,
        english_translation=seed.english_translation,
        word_class=seed.word_class,
        gender=seed.gender,
        plural_form=seed.plural_form,
        example_sentence_de=seed.example_sentence_de,
        example_sentence_en=seed.example_sentence_en,
        mnemonic=seed.mnemonic,
        gender_tip=seed.gender_tip,
        source=f"{level.upper()} library",
        tags=[level.upper()],
        difficulty=None,
        next_review=None,
        created_at=date.today().isoformat(),
        seeded_from=word_id,
    )
    db.add(card)
    db.commit()
    return {**card.to_dict(), "activated": True}


@router.post("/{level}/activate-lesson")
def activate_lesson(level: str, body: ActivateLessonRequest, db: Session = Depends(get_db)):
    seeds = db.query(SeedWord).filter(
        SeedWord.level == level.upper(),
        SeedWord.lesson_number == body.lesson_number,
    ).all()

    if not seeds:
        raise HTTPException(status_code=404, detail="No words found for that lesson")

    activated_ids = {
        row[0]
        for row in db.query(Flashcard.seeded_from).filter(Flashcard.seeded_from.isnot(None)).all()
    }
    existing_words = {row[0] for row in db.query(Flashcard.german_word).all()}

    added = linked = 0
    for seed in seeds:
        if seed.id in activated_ids:
            continue
        if seed.german_word in existing_words:
            card = db.query(Flashcard).filter(Flashcard.german_word == seed.german_word).first()
            if card:
                card.seeded_from = seed.id
                linked += 1
        else:
            db.add(Flashcard(
                id=str(uuid.uuid4()),
                german_word=seed.german_word,
                english_translation=seed.english_translation,
                word_class=seed.word_class,
                gender=seed.gender,
                plural_form=seed.plural_form,
                example_sentence_de=seed.example_sentence_de,
                example_sentence_en=seed.example_sentence_en,
                mnemonic=seed.mnemonic,
                gender_tip=seed.gender_tip,
                source=f"{level.upper()} library",
                tags=[level.upper()],
                difficulty=None,
                next_review=None,
                created_at=date.today().isoformat(),
                seeded_from=seed.id,
            ))
            added += 1

    db.commit()
    return {"added": added, "linked": linked, "skipped": len(seeds) - added - linked}


@router.post("/{level}/activate-bulk")
def activate_bulk(level: str, body: BulkActivateRequest, db: Session = Depends(get_db)):
    level_upper = level.upper()
    activated_ids = {
        row[0] for row in
        db.query(Flashcard.seeded_from).filter(Flashcard.seeded_from.isnot(None)).all()
    }
    added = linked = skipped = 0
    for word_id in body.word_ids:
        if word_id in activated_ids:
            skipped += 1
            continue
        seed = db.query(SeedWord).filter(
            SeedWord.id == word_id, SeedWord.level == level_upper
        ).first()
        if not seed:
            skipped += 1
            continue
        existing = db.query(Flashcard).filter(Flashcard.german_word == seed.german_word).first()
        if existing:
            existing.seeded_from = seed.id
            linked += 1
        else:
            db.add(Flashcard(
                id=str(uuid.uuid4()),
                german_word=seed.german_word,
                english_translation=seed.english_translation,
                word_class=seed.word_class,
                gender=seed.gender,
                plural_form=seed.plural_form,
                example_sentence_de=seed.example_sentence_de,
                example_sentence_en=seed.example_sentence_en,
                mnemonic=seed.mnemonic,
                gender_tip=seed.gender_tip,
                source=f"{level_upper} library",
                tags=[level_upper],
                difficulty=None,
                next_review=None,
                created_at=date.today().isoformat(),
                seeded_from=seed.id,
            ))
            added += 1
    db.commit()
    return {"added": added, "linked": linked, "skipped": skipped}
