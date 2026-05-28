"""
Generic German vocabulary PDF parser for CEFR word lists (A1, A2, B1, ...).

Handles multiple common PDF formats:
  - TELC word lists (inline L1/L2/... lesson tags)
  - Goethe-Institut lists (Lektion 1, Kapitel 1, Thema 1 headers)
  - Plain alphabetical lists (no lessons — groups everything as Lesson 1)

Usage:
    python parse_pdf.py --input path/to/wordlist.pdf --level A1
    python parse_pdf.py --input path/to/wordlist.pdf --level A2 --output seed_data/A2/input.txt

Output is written to seed_data/{LEVEL}/input.txt by default.
Inspect the output before running generate_seed_data.py — edit lesson names if needed.
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("PyMuPDF not found. Install with: pip install pymupdf")
    sys.exit(1)

# Articles to strip from the front of words
_ARTICLES = ("der ", "die ", "das ", "Der ", "Die ", "Das ",
             "ein ", "eine ", "Ein ", "Eine ")

# Lines that are obviously not words
_SKIP_RE = re.compile(
    r"^(AGB|BRD|DDR|EU|NATO|DVD|PC|WM|Pl\.|ugs\.|bzw\.|usw\.|etc\.|z\.B\.)$",
    re.IGNORECASE,
)

# Lesson heading patterns — matched in order of specificity
_LESSON_PATTERNS = [
    re.compile(r"^L(\d{1,2})$"),                          # TELC: L1, L12
    re.compile(r"^Lektion\s+(\d{1,2})", re.IGNORECASE),   # Lektion 3
    re.compile(r"^Kapitel\s+(\d{1,2})", re.IGNORECASE),   # Kapitel 3
    re.compile(r"^Thema\s+(\d{1,2})", re.IGNORECASE),     # Thema 3
    re.compile(r"^Lesson\s+(\d{1,2})", re.IGNORECASE),    # Lesson 3
    re.compile(r"^Unit\s+(\d{1,2})", re.IGNORECASE),      # Unit 3
    re.compile(r"^(\d{1,2})\.\s+[A-ZÄÖÜ]"),              # "3. Familie"
]

# Lines to skip wholesale
_IGNORE_RE = re.compile(
    r"(Wortschatzliste|Wortliste|Wortschatz|Vokabeln|Inhalt|Seite|Impressum"
    r"|Lernziele|Grammatik|Phonetik|Bildquelle|©|www\.|ISBN)",
    re.IGNORECASE,
)


def _match_lesson(line: str) -> int | None:
    """Return lesson number if the line looks like a lesson heading, else None."""
    s = line.strip()
    for pat in _LESSON_PATTERNS:
        m = pat.match(s)
        if m:
            return int(m.group(1))
    return None


def _clean_word(raw: str) -> str | None:
    word = raw.strip().rstrip("\t,;.").strip()
    if not word or len(word) <= 1:
        return None
    if _SKIP_RE.match(word):
        return None
    if _IGNORE_RE.search(word):
        return None
    # Skip lines that are clearly page numbers or single uppercase letters
    if re.match(r"^\d+$", word) or re.match(r"^[A-ZÄÖÜ]$", word):
        return None
    # Skip lines that are too long to be a single word/phrase (probably running text)
    if len(word.split()) > 5:
        return None
    # Strip articles
    for art in _ARTICLES:
        if word.startswith(art):
            word = word[len(art):]
            break
    # Take only first part if slash-separated variants given (e.g. "gehen/fahren")
    word = word.split("/")[0].strip()
    # Remove trailing grammar notes in parentheses: "laufen (ist gelaufen)"
    word = re.sub(r"\s*\(.*\)$", "", word).strip()
    return word if word else None


def extract_words(pdf_path: Path, level: str) -> dict[int, list[str]]:
    doc = fitz.open(str(pdf_path))
    all_lines: list[str] = []
    for page in doc:
        all_lines.extend(page.get_text("text").splitlines())
    doc.close()

    by_lesson: dict[int, list[str]] = {}
    current_lesson = 1

    for line in all_lines:
        lesson_num = _match_lesson(line)
        if lesson_num is not None:
            current_lesson = lesson_num
            continue

        word = _clean_word(line)
        if word:
            by_lesson.setdefault(current_lesson, []).append(word)

    return by_lesson


def write_output(by_lesson: dict[int, list[str]], output_path: Path) -> None:
    lines = []
    for lesson_num in sorted(by_lesson):
        lines.append(f"Lesson {lesson_num}")
        seen: set[str] = set()
        for word in by_lesson[lesson_num]:
            if word.lower() not in seen:
                lines.append(word)
                seen.add(word.lower())
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    total = sum(len(v) for v in by_lesson.values())
    print(f"\nExtracted {total} words across {len(by_lesson)} lessons → {output_path}")
    for ln in sorted(by_lesson):
        words = by_lesson[ln]
        unique = len({w.lower() for w in words})
        print(f"  Lesson {ln:2d}: {unique} words")

    print("\nTip: open the output file and rename 'Lesson N' lines to descriptive")
    print("     topic names before running generate_seed_data.py")


def main():
    parser = argparse.ArgumentParser(description="Parse German vocabulary PDF into input.txt")
    parser.add_argument("--input",  required=True, help="Path to PDF word list")
    parser.add_argument("--level",  required=True, help="CEFR level, e.g. A1")
    parser.add_argument("--output", default=None,  help="Output path (default: seed_data/{LEVEL}/input.txt)")
    args = parser.parse_args()

    pdf_path    = Path(args.input)
    level       = args.level.upper()
    output_path = Path(args.output) if args.output else Path(f"seed_data/{level}/input.txt")

    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    print(f"Parsing {pdf_path} ...")
    by_lesson = extract_words(pdf_path, level)

    if not by_lesson:
        print("No words extracted. The PDF may use an unusual format.")
        print("Try opening it and checking the text structure manually.")
        sys.exit(1)

    write_output(by_lesson, output_path)


if __name__ == "__main__":
    main()
