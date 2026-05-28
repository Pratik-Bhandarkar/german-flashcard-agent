"""
End-to-end tests for the spaced repetition feature.
Inserts test cards directly into the DB (bypasses the pipeline).
Cleans up all created cards after every run.

Usage:
    python test_spaced_repetition.py
"""

import sys
import uuid
import datetime
import requests

# Bootstrap Django-style so we can import project modules directly
sys.path.insert(0, ".")
from backend.database.db import SessionLocal
from backend.database.models import Flashcard

BASE = "http://localhost:8000"
PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
BUG  = "\033[91mBUG \033[0m"
INFO = "\033[94mINFO\033[0m"

results  = []
test_ids = []
_log_lines = []

import io as _io

def _emit(line):
    print(line)
    _log_lines.append(line)

def check(label, condition, detail=""):
    tag    = PASS if condition else FAIL
    status = "PASS" if condition else "FAIL"
    _emit(f"  [{tag}] {label}")
    if detail:
        _emit(f"         {detail}")
    results.append((status, label, detail))
    return condition

def bug(label, detail=""):
    _emit(f"  [{BUG}] {label}")
    if detail:
        _emit(f"         {detail}")
    results.append(("BUG", label, detail))

def section(title):
    _emit(f"\n{'='*60}")
    _emit(f"  {title}")
    _emit('='*60)


def offset(days):
    return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()


def today():
    return datetime.date.today().isoformat()


def purge_test_cards():
    """Remove any _test_* leftovers from a previous crashed run."""
    db = SessionLocal()
    try:
        rows = db.query(Flashcard).filter(
            Flashcard.german_word.like("_test_%")
        ).all()
        for row in rows:
            db.delete(row)
        db.commit()
        if rows:
            print(f"  [{INFO}] Purged {len(rows)} leftover test card(s) from a previous run")
    finally:
        db.close()


def insert_card(next_review=None, difficulty=None, suffix=None):
    """Insert a minimal but valid flashcard directly into the DB."""
    card_id   = str(uuid.uuid4())
    word_slug = suffix or card_id[:8]
    db = SessionLocal()
    try:
        card = Flashcard(
            id=card_id,
            german_word=f"_test_{word_slug}",
            english_translation="test word",
            word_class="noun",
            gender="der",
            example_sentence_de="Das ist ein Testwort.",
            example_sentence_en="This is a test word.",
            created_at=today(),
            difficulty=difficulty,
            next_review=next_review,
        )
        db.add(card)
        db.commit()
        test_ids.append(card_id)
        return card_id
    finally:
        db.close()


def get_review_ids():
    r = requests.get(f"{BASE}/flashcards/review", timeout=5)
    return {c["id"] for c in r.json()}


def get_card(card_id):
    r = requests.get(f"{BASE}/flashcards/{card_id}", timeout=5)
    return r.json() if r.status_code == 200 else None


# ── preflight ────────────────────────────────────────────────
section("PREFLIGHT")
try:
    r = requests.get(f"{BASE}/health", timeout=3)
    check("Server running", r.status_code == 200)
except Exception as e:
    print(f"  [{FAIL}] Cannot reach server: {e}")
    sys.exit(1)

purge_test_cards()


# ── 1. REVIEW FILTER ─────────────────────────────────────────
section("1. REVIEW FILTER — which cards appear in /review")
print(f"  [{INFO}] Today is {today()}")

id_null      = insert_card(next_review=None,        suffix="null")
id_today     = insert_card(next_review=offset(0),   suffix="today")
id_yesterday = insert_card(next_review=offset(-1),  suffix="yesterday")
id_overdue   = insert_card(next_review=offset(-7),  suffix="overdue")
id_tomorrow  = insert_card(next_review=offset(+1),  suffix="tomorrow")
id_future    = insert_card(next_review=offset(+7),  suffix="future")

due = get_review_ids()

check("next_review = null      => in queue (never studied)", id_null      in due)
check("next_review = today     => in queue (due today)",     id_today     in due)
check("next_review = yesterday => in queue (overdue -1d)",   id_yesterday in due)
check("next_review = -7 days   => in queue (overdue -7d)",   id_overdue   in due)
check("next_review = +1 day    => NOT in queue",             id_tomorrow  not in due)
check("next_review = +7 days   => NOT in queue",             id_future    not in due)


# ── 2. DIFFICULTY SCHEDULING ─────────────────────────────────
section("2. DIFFICULTY SCHEDULING — PUT stores correct next_review")

schedule_id = insert_card(next_review=None, suffix="sched")

cases = [
    ("easy",   offset(+7)),
    ("medium", offset(+3)),
    ("hard",   offset(+1)),
]

for difficulty, expected_date in cases:
    r = requests.put(
        f"{BASE}/flashcards/{schedule_id}",
        json={"difficulty": difficulty, "next_review": expected_date},
        timeout=5
    )
    stored = r.json().get("next_review") if r.status_code == 200 else None
    days   = {"easy": 7, "medium": 3, "hard": 1}[difficulty]
    check(
        f"difficulty='{difficulty}' => next_review = today+{days}d stored correctly",
        stored == expected_date,
        f"expected {expected_date!r}  got {stored!r}"
    )


# ── 3. CARD LEAVES QUEUE AFTER RATING ────────────────────────
section("3. CARD LEAVES REVIEW QUEUE AFTER RATING")

leave_id = insert_card(next_review=offset(0), suffix="leave")
check("card starts in queue (next_review=today)", leave_id in get_review_ids())

r = requests.put(
    f"{BASE}/flashcards/{leave_id}",
    json={"difficulty": "easy", "next_review": offset(+7)},
    timeout=5
)
check(
    "card rated 'easy' (next_review=+7d) => no longer in queue",
    leave_id not in get_review_ids(),
    f"PUT status={r.status_code}"
)

hard_id = insert_card(next_review=offset(-2), suffix="hard")
check("overdue card starts in queue", hard_id in get_review_ids())

requests.put(
    f"{BASE}/flashcards/{hard_id}",
    json={"difficulty": "hard", "next_review": offset(+1)},
    timeout=5
)
check(
    "card rated 'hard' (next_review=tomorrow) => no longer in queue",
    hard_id not in get_review_ids()
)


# ── 4. CARD REAPPEARS AFTER DATE PASSES ──────────────────────
section("4. CARD REAPPEARS — simulate date passing by backdating")

future_id = insert_card(next_review=offset(+7), suffix="reappear")
check("card with next_review=+7d is NOT in queue", future_id not in get_review_ids())

# Simulate the 7 days passing by backdating to yesterday
requests.put(
    f"{BASE}/flashcards/{future_id}",
    json={"next_review": offset(-1)},
    timeout=5
)
check(
    "same card after backdating => reappears in queue",
    future_id in get_review_ids()
)


# ── 5. DIFFICULTY VALIDATION ─────────────────────────────────
section("5. DIFFICULTY VALIDATION — enum enforced by API")

val_id = insert_card(suffix="val")
for bad in ["EASY", "veryhard", "1", "null", "yes"]:
    r = requests.put(f"{BASE}/flashcards/{val_id}", json={"difficulty": bad}, timeout=5)
    check(f"difficulty={bad!r} => 422", r.status_code == 422, f"status={r.status_code}")

for good in ["easy", "medium", "hard"]:
    r = requests.put(f"{BASE}/flashcards/{val_id}", json={"difficulty": good}, timeout=5)
    check(f"difficulty={good!r} => 200", r.status_code == 200, f"status={r.status_code}")


# ── 6. NEXT_REVIEW DATE VALIDATION ───────────────────────────
section("6. NEXT_REVIEW VALIDATION — ISO date enforced")

date_id = insert_card(suffix="date")
for bad in ["not-a-date", "28-05-2026", "2026/05/28", "tomorrow", "0", "2026-13-01"]:
    r = requests.put(f"{BASE}/flashcards/{date_id}", json={"next_review": bad}, timeout=5)
    check(f"next_review={bad!r} => 422", r.status_code == 422, f"status={r.status_code}")

r = requests.put(f"{BASE}/flashcards/{date_id}", json={"next_review": offset(+3)}, timeout=5)
check(f"next_review={offset(+3)!r} (valid ISO) => 200", r.status_code == 200)


# ── 7. TIMEZONE BUG IN FRONTEND ──────────────────────────────
section("7. TIMEZONE BUG — Study.jsx getNextReviewDate")

# Reproduce the exact frontend JS logic in Python:
#   const today = new Date()
#   today.setDate(today.getDate() + days[difficulty])
#   return today.toISOString().split('T')[0]       ← BUG: uses UTC, not local

utc_offset_s = (datetime.datetime.now() - datetime.datetime.utcnow()).total_seconds()
utc_offset_h = round(utc_offset_s / 3600, 1)
print(f"  [{INFO}] Local UTC offset: UTC{utc_offset_h:+.1f}h")

def frontend_buggy_date(days_ahead):
    """Simulate the buggy JS: adds days, then converts to UTC ISO string."""
    future_local = datetime.datetime.now() + datetime.timedelta(days=days_ahead)
    # toISOString() shifts to UTC
    future_utc = future_local - datetime.timedelta(seconds=utc_offset_s)
    return future_utc.strftime("%Y-%m-%d")

def frontend_correct_date(days_ahead):
    return (datetime.date.today() + datetime.timedelta(days=days_ahead)).isoformat()

days_map = {"easy": 7, "medium": 3, "hard": 1}
found_mismatch = False
for diff, days in days_map.items():
    buggy   = frontend_buggy_date(days)
    correct = frontend_correct_date(days)
    if buggy != correct:
        found_mismatch = True
        bug(
            f"'{diff}' date wrong: JS gives {buggy!r}, correct is {correct!r}",
            "toISOString() converts to UTC before splitting => off by 1 day in UTC+ zones after ~22:00."
        )

if not found_mismatch:
    if utc_offset_h > 0:
        bug(
            f"Latent timezone bug in Study.jsx:8 (UTC{utc_offset_h:+.1f}h, harmless right now)",
            f"After {24 - utc_offset_h:.0f}:00 local time, toISOString() gives yesterday's date. "
            "Fix: use local date arithmetic instead of toISOString()."
        )
    else:
        check("No UTC offset — timezone bug does not apply", True)


# ── 8. STUDY-AGAIN DOES NOT RESET SCHEDULING ─────────────────
section("8. STUDY-AGAIN FLOW — reviewed cards keep their schedule")

# After studying, cards are already scheduled (next_review > today).
# If user clicks "Study Again", they get those same cards back.
# The session re-fetches ALL cards (not just due ones) — this is intentional.
# Verify the cards still have the correct next_review after the second rating.

replay_id = insert_card(next_review=offset(+5), difficulty="medium", suffix="replay")

# Simulate re-rating the same card again (Study Again scenario)
r = requests.put(
    f"{BASE}/flashcards/{replay_id}",
    json={"difficulty": "easy", "next_review": offset(+7)},
    timeout=5
)
stored = r.json() if r.status_code == 200 else {}
check(
    "Re-rating a card updates difficulty and next_review cleanly",
    stored.get("difficulty") == "easy" and stored.get("next_review") == offset(+7),
    f"difficulty={stored.get('difficulty')!r}  next_review={stored.get('next_review')!r}"
)


# ── cleanup ──────────────────────────────────────────────────
section("CLEANUP")
deleted = 0
for cid in test_ids:
    r = requests.delete(f"{BASE}/flashcards/{cid}", timeout=5)
    if r.status_code == 200:
        deleted += 1
print(f"  [{INFO}] Deleted {deleted}/{len(test_ids)} test cards")


# ── summary ──────────────────────────────────────────────────
section("SUMMARY")
total  = len(results)
passed = sum(1 for s,_,_ in results if s == "PASS")
failed = sum(1 for s,_,_ in results if s == "FAIL")
bugs   = sum(1 for s,_,_ in results if s == "BUG")

print(f"  Total : {total}")
print(f"  \033[92mPASS\033[0m  : {passed}")
print(f"  \033[91mFAIL\033[0m  : {failed}  <- unexpected")
print(f"  \033[91mBUG \033[0m  : {bugs}  <- needs fixing")

if failed or bugs:
    _emit(f"\n  Issues:")
    for s, label, detail in results:
        if s in ("FAIL", "BUG"):
            _emit(f"    [{s}] {label}")
            if detail:
                _emit(f"           {detail.splitlines()[0]}")

# Write plain-text log for the Read tool
import re as _re
plain = _re.sub(r'\033\[[0-9;]*m', '', '\n'.join(_log_lines))
with open("test_sr_results.txt", "w", encoding="utf-8") as f:
    f.write(plain)

