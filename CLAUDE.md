# Wortblitz — Claude Code Project Guide

## What this is
A personal German vocabulary flashcard app with spaced repetition. Single user (the owner).
Built with FastAPI backend, LangGraph enrichment pipeline, and React/Tailwind frontend.

## Dev commands

**Backend** (from project root, with venv activated):
```
uvicorn backend.main:app --reload
```

**Frontend:**
```
cd frontend && npm run dev
```

**Seed data enrichment** (one-off, takes ~60 min per level):
```
python generate_seed_data.py --input seed_data/A1/input.txt --level A1
```

**Load enriched seed data into DB:**
```
python -m backend.database.seed_loader
```

## Tech stack
- **Backend:** FastAPI + SQLAlchemy + SQLite (`data/flashcards.db`)
- **Pipeline:** LangGraph (parser → enrichment → validator → storage)
- **LLM:** OpenAI gpt-4o-mini via `USE_LOCAL_LLM=false` in `.env`
- **Translation:** DeepL API
- **Frontend:** React 19 + Vite + Tailwind CSS
- **Speech:** Web Speech API (browser-native, no API key)

## Project structure
```
backend/
  main.py               — FastAPI app, CORS, security headers middleware
  routes/
    flashcards.py       — All flashcard CRUD + pipeline trigger endpoints
    library.py          — Vocabulary library (seed words, level browsing, activation)
  database/
    models.py           — SQLAlchemy models: Flashcard, SeedWord
    db.py               — DB init, migrations, session
    seed_loader.py      — Loads seed_data/*/words.json into seed_words table
pipeline/
  config.py             — All API keys and feature flags (reads from .env)
  graph.py              — LangGraph pipeline definition
  agents/               — parser, enrichment, validator, storage agents
  tools/
    deepl_client.py     — DeepL translation wrapper
    llm_client.py       — OpenAI/Ollama LLM wrapper
frontend/src/
  pages/                — Home, Study, Translate, Add, Library, LibraryLevel
  services/api.js       — ALL API calls go here (never call axios directly in pages)
  utils/
    speech.js           — speak() and cancelSpeech() — Web Speech API wrapper
    srs.js              — getNextReviewDate() — spaced repetition intervals
seed_data/
  A1/, A2/, B1/         — input.txt (parsed word list) + words.json (enriched)
```

## Data model

### `flashcards` — active study deck
Cards the user is actively studying. Created by:
- Activating a word from the Library (`seeded_from` is set)
- Running Add Vocab / Translate pipeline (`source = "manual input"` or `"translator"`)

Key fields: `german_word`, `english_translation`, `gender`, `word_class`, `difficulty`,
`next_review`, `last_reviewed`, `seeded_from`, `source`, `tags`

### `seed_words` — vocabulary library (read-only catalogue)
Pre-enriched word catalogue. Not in the deck until activated.
Key fields: `id` (e.g. `a1_007`), `level` (A1/A2/B1), `lesson`, `lesson_number`

## Key conventions
- All API calls from the frontend go through `frontend/src/services/api.js`
- Never hardcode the API URL — use `import.meta.env.VITE_API_BASE_URL`
- `source = "translator"` cards are excluded from the main study queue (they go to the Translation Deck on the Translate page)
- Spaced repetition intervals: hard = +1 day, medium = +3 days, easy = +7 days
- Session cap: 20 cards per study session (reviews first, then new cards)
- `_TRANSLATOR_SOURCE = "translator"` constant in flashcards.py — never hardcode the string
- `CefrLevel = Literal["A1"..."C2"]` type in library.py — use it for all level path params

## Vocabulary levels
- **A1** — 954 enriched words, 12 lessons (Einfach gut series)
- **A2** — 972 enriched words, 12 lessons (Einfach gut series)
- **B1** — 920 enriched words, 11 lessons (TELC series)
- **B2/C1/C2** — locked (no seed data yet)

## Features
- Flip card study with spaced repetition (Hard/Medium/Easy)
- Auto-play German pronunciation on each card (Web Speech API, rate 0.6)
- Auto-enroll next lesson when all cards in current lesson are reviewed
- Translation Deck — separate from main study queue, lives on Translate page
- Words of the Day — 3 daily rotating cards from all unlocked levels
- Library browsing with lesson-by-lesson activation

## Product backlog
- User-editable mnemonics (API already supports it via PATCH — just needs UI)
- Authentication before any public deployment (currently no auth)
- Rate limiting on DeepL/OpenAI endpoints (currently no throttle)
- Magic byte file type validation (currently extension-only)

## Environment variables (.env)
```
USE_LOCAL_LLM=false
OPENAI_API_KEY=...
DEEPL_API_KEY=...
DATABASE_PATH=data/flashcards.db
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
ALLOWED_ORIGINS=http://localhost:5173
```
