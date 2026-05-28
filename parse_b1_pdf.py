"""
Parses the TELC B1 alphabetical word list PDF into a lesson-grouped word list
that generate_seed_data.py can consume.

Usage:
    python parse_b1_pdf.py --input path/to/b1_wordlist.pdf --output seed_data/b1_input.txt
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

LESSON_TOPICS = {
    1:  "Reisen und Unterwegs",
    2:  "Wohnen und Zusammenleben",
    3:  "Umwelt und Natur",
    4:  "Online-Shopping",
    5:  "Freizeit und Sport",
    6:  "Geschichte und Gesellschaft",
    7:  "Sprache und Kommunikation",
    8:  "Beruf und Karriere",
    9:  "Buero und Alltag",
    10: "Ernaehrung und Gesundheit",
    11: "Auto und Verkehr",
}

LESSON_TAG_RE = re.compile(r"^L(\d{1,2})$")
SKIP_RE = re.compile(r"^(AGB|BRD|DDR|EU|NATO|DVD|PC|WM|Pl\.|ugs\.)$", re.IGNORECASE)


def _clean_word(raw: str) -> str | None:
    word = raw.strip().rstrip("\t").strip()
    if not word or len(word) <= 1:
        return None
    if SKIP_RE.match(word):
        return None
    if "=" in word:
        return None
    word = word.split("/")[0].strip()
    for art in ("der ", "die ", "das ", "Der ", "Die ", "Das "):
        if word.startswith(art):
            word = word[len(art):]
            break
    return word if word else None


def extract_entries(pdf_path: Path) -> list[tuple[str, int]]:
    doc = fitz.open(str(pdf_path))
    all_lines: list[str] = []

    for page in doc:
        text = page.get_text("text")
        all_lines.extend(text.splitlines())

    doc.close()

    entries: list[tuple[str, int]] = []
    i = 0
    pending_word_parts: list[str] = []

    while i < len(all_lines):
        line = all_lines[i]
        tag_m = LESSON_TAG_RE.match(line.strip())

        if tag_m:
            lesson_num = int(tag_m.group(1))
            if pending_word_parts:
                raw = " ".join(pending_word_parts)
                word = _clean_word(raw)
                if word:
                    entries.append((word, lesson_num))
            pending_word_parts = []
        elif line.strip() and not re.match(r"^\d+$", line.strip()) \
                and "Wortschatzliste" not in line \
                and not re.match(r"^[A-Z]$", line.strip()):
            pending_word_parts.append(line.strip().rstrip("\t"))

        i += 1

    return entries


def write_word_list(entries: list[tuple[str, int]], output_path: Path) -> None:
    by_lesson: dict[int, list[str]] = {}
    for word, lesson in entries:
        by_lesson.setdefault(lesson, []).append(word)

    lines = []
    for lesson_num in sorted(by_lesson):
        topic = LESSON_TOPICS.get(lesson_num, f"Lesson {lesson_num}")
        lines.append(f"Lesson {lesson_num} — {topic}")
        seen: set[str] = set()
        for word in by_lesson[lesson_num]:
            if word.lower() not in seen:
                lines.append(word)
                seen.add(word.lower())
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    total = sum(len(v) for v in by_lesson.values())
    print(f"Extracted {total} words across {len(by_lesson)} lessons -> {output_path}")
    for ln in sorted(by_lesson):
        print(f"  L{ln:2d}: {len(by_lesson[ln])} words")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  required=True)
    parser.add_argument("--output", default="seed_data/B1/input.txt")
    args = parser.parse_args()

    pdf_path = Path(args.input)
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    entries = extract_entries(pdf_path)
    write_word_list(entries, Path(args.output))


if __name__ == "__main__":
    main()
