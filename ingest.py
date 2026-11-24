"""Read the linked reporting notes and preserve the boundaries between observations."""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {s["id"]: s for s in json.loads((ROOT / "sources.json").read_text())}


def windows(words, size, overlap):
    for start in range(0, len(words), size - overlap):
        yield " ".join(words[start:start + size])
        if start + size >= len(words):
            break


def chunks(strategy="paragraph"):
    for source in SOURCES:
        raw = (ROOT / "documents" / f"{source}.txt").read_text(encoding="utf-8")
        raw = unicodedata.normalize("NFKC", raw).strip()
        sections = re.split(r"\n\s*\n", raw) if strategy == "paragraph" else [raw]
        index = 0
        for section in sections:
            size, overlap = (75, 12) if strategy == "paragraph" else (12, 0)
            for passage in windows(section.split(), size, overlap):
                index += 1
                yield f"{source}-{index:02}", source, index, passage
