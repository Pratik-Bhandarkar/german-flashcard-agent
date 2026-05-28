"""
Parser for the "Einfach gut" series alphabetical word lists (A1, A2).

Format: each entry is "Word  L<num>" where the lesson number sits next to the word.
This differs from the B1 TELC format where lesson tags appear as standalone lines.

Usage:
    python parse_einfach_gut.py --input path/to/A1_wordlist.pdf --level A1
    python parse_einfach_gut.py --input path/to/A2_wordlist.pdf --level A2

Output: seed_data/{LEVEL}/input.txt  (consumed by generate_seed_data.py)
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import fitz
except ImportError:
    print("PyMuPDF not found. Install with: pip install pymupdf")
    sys.exit(1)

# ── Lesson topic names ────────────────────────────────────────────────────────

_TOPICS = {
    "A1": {
        1:  "Hallo",
        2:  "Ich bin neu hier",
        3:  "Im Kursraum",
        4:  "Essen und Trinken",
        5:  "Mein Tag",
        6:  "Wohnen",
        7:  "In der Stadt",
        8:  "Berufe",
        9:  "Gesundheit",
        10: "Reisen und Urlaub",
        11: "Kleidung und Mode",
        12: "Feste und Jahreszeiten",
    },
    "A2": {
        1:  "Online und vernetzt",
        2:  "Mit der Bahn unterwegs",
        3:  "Wohnen und Nachbarschaft",
        4:  "Ämter und Dokumente",
        5:  "Bildung und Ausbildung",
        6:  "Arbeit und Berufe",
        7:  "Shopping und Einkaufen",
        8:  "Im Betrieb",
        9:  "Schule und Lernen",
        10: "Gesundheit und Fitness",
        11: "Geld und Finanzen",
        12: "Freizeit und Feste",
    },
}

# ── Words that are not useful as vocabulary flashcards ────────────────────────

_SKIP_WORDS = {
    # articles
    "der", "die", "das", "ein", "eine", "einer", "einem", "einen", "eines",
    # personal pronouns
    "ich", "du", "er", "sie", "es", "wir", "ihr",
    "mich", "mir", "dich", "dir", "ihn", "ihm", "uns", "euch", "sich",
    "ihnen",
    # demonstrative / indefinite pronouns
    "man", "alles", "etwas", "jeder",
    # possessives (short forms)
    "mein", "dein", "sein", "unser",
    # basic prepositions
    "ab", "an", "auf", "aus", "bei", "bis", "durch", "für",
    "gegen", "in", "mit", "nach", "neben", "ohne", "über",
    "um", "unter", "von", "vor", "zu", "zwischen",
    # conjunctions / particles
    "aber", "also", "als", "auch", "bevor", "da", "damit", "dann",
    "dass", "denn", "doch", "oder", "seit", "so", "sondern",
    "trotzdem", "und", "weil", "wenn",
    # question words
    "warum", "was", "wer", "wie", "wo", "woher", "wohin", "wann",
    # basic adverbs / filler
    "bald", "bitte", "danke", "dort", "ganz", "gern", "gut",
    "hier", "immer", "ja", "jetzt", "nein", "nie", "noch",
    "nur", "oft", "schon", "sehr", "sofort", "tschüss",
    "wieder", "zuerst",
    # grammar meta-terms (from the word list headers)
    "l1", "l2", "l3", "l4", "l5", "l6", "l7", "l8", "l9", "l10", "l11", "l12",
}

# ── Regex patterns ────────────────────────────────────────────────────────────

# Matches e.g. "Abend L1" or "Hals-Nasen-Ohren-Arzt (HNO) L9"
_WORD_WITH_LESSON = re.compile(
    r"^(.+?)\s+L(\d{1,2})\s*$",
    re.UNICODE,
)
# Matches a bare "L1" line (word was on previous line)
_BARE_LESSON = re.compile(r"^L(\d{1,2})\s*$")

# Lines that are obviously not vocabulary entries
_SKIP_LINE = re.compile(
    r"(Wortschatzliste|Alphabetische|^\d+$|^[A-ZÄÖÜ]$)",
    re.IGNORECASE,
)

_ARTICLES = ("der ", "die ", "das ", "Der ", "Die ", "Das ")


def _clean(raw: str) -> str | None:
    word = raw.strip().rstrip(".,;").strip()
    if not word or len(word) <= 1:
        return None
    if _SKIP_LINE.search(word):
        return None
    # Strip leading article
    for art in _ARTICLES:
        if word.startswith(art):
            word = word[len(art):]
            break
    # Remove grammar notes in parentheses: "laufen (ist gelaufen)" → "laufen"
    word = re.sub(r"\s*\(.*?\)\s*$", "", word).strip()
    # Remove trailing slash variants: "Arzt/Ärztin" → "Arzt"
    word = word.split("/")[0].strip()
    # Skip if all-lowercase single-syllable function word
    if word.lower() in _SKIP_WORDS:
        return None
    # Skip lines that are too long (sentence fragments)
    if len(word.split()) > 6:
        return None
    return word or None


def extract(pdf_path: Path) -> dict[int, list[str]]:
    doc = fitz.open(str(pdf_path))
    lines: list[str] = []
    for page in doc:
        lines.extend(page.get_text("text").splitlines())
    doc.close()

    by_lesson: dict[int, list[str]] = {}
    pending: str | None = None

    for line in lines:
        line = line.strip()
        if not line:
            pending = None
            continue

        # "Word L<num>" on one line
        m = _WORD_WITH_LESSON.match(line)
        if m:
            word = _clean(m.group(1))
            lesson = int(m.group(2))
            if word:
                by_lesson.setdefault(lesson, []).append(word)
            pending = None
            continue

        # Just "L<num>" — pair with pending word
        m = _BARE_LESSON.match(line)
        if m:
            lesson = int(m.group(1))
            if pending:
                word = _clean(pending)
                if word:
                    by_lesson.setdefault(lesson, []).append(word)
            pending = None
            continue

        # Might be a word waiting for its lesson number on next line
        if not _SKIP_LINE.search(line):
            pending = line
        else:
            pending = None

    return by_lesson


def write_output(by_lesson: dict[int, list[str]], output_path: Path, level: str) -> None:
    topics = _TOPICS.get(level, {})
    lines = []
    total = 0

    for lesson_num in sorted(by_lesson):
        topic = topics.get(lesson_num, f"Lesson {lesson_num}")
        lines.append(f"Lesson {lesson_num} — {topic}")
        seen: set[str] = set()
        for word in by_lesson[lesson_num]:
            if word.lower() not in seen:
                lines.append(word)
                seen.add(word.lower())
                total += 1
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"\n{level} — {total} words across {len(by_lesson)} lessons → {output_path}")
    for ln in sorted(by_lesson):
        topic = topics.get(ln, f"Lesson {ln}")
        unique = len({w.lower() for w in by_lesson[ln]})
        print(f"  L{ln:2d} {topic:<35} {unique} words")


def main():
    parser = argparse.ArgumentParser(
        description="Parse Einfach-gut A1/A2 alphabetical word list PDF"
    )
    parser.add_argument("--input",  required=True, help="Path to the PDF")
    parser.add_argument("--level",  required=True, help="CEFR level: A1 or A2")
    parser.add_argument("--output", default=None,  help="Output path (default: seed_data/{LEVEL}/input.txt)")
    args = parser.parse_args()

    pdf_path    = Path(args.input)
    level       = args.level.upper()
    output_path = Path(args.output) if args.output else Path(f"seed_data/{level}/input.txt")

    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    print(f"Parsing {pdf_path} ...")
    by_lesson = extract(pdf_path)

    if not by_lesson:
        print("No words extracted — check the PDF format.")
        sys.exit(1)

    write_output(by_lesson, output_path, level)
    print("\nDone. Run generate_seed_data.py next:")
    print(f"  python generate_seed_data.py --input {output_path} --level {level}")


if __name__ == "__main__":
    main()
