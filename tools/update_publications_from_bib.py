from __future__ import annotations

import re
from pathlib import Path

import bibtexparser

ROOT = Path(__file__).resolve().parent.parent
BIB_FILE = ROOT / "files" / "citations.bib"
HTML_FILE = ROOT / "publications.html"

JOURNAL_TYPES = {"article", "book", "chapter", "mastersthesis", "phdthesis"}
CONFERENCE_TYPES = {"inproceedings", "conference", "proceedings", "techreport"}

ENTRY_TEMPLATE = """    <article class=\"publication-entry\">\n      <h3><a href=\"./files/citations.bib#{key}\">{title}</a></h3>\n      <p class=\"publication-authors\">{authors}</p>\n      <p class=\"publication-meta\">{meta}</p>\n    </article>"""


def sanitize_title(text: str) -> str:
    return text.replace("\n", " ").strip()


def format_authors(author_field: str) -> str:
    if not author_field:
        return ""
    authors = [a.strip() for a in author_field.replace("\n", " ").split(" and ")]
    return " · ".join([a for a in authors if a])


def build_meta(entry: dict) -> str:
    year = entry.get("year", "").strip()
    journal = entry.get("journal") or entry.get("booktitle") or entry.get("publisher") or ""
    parts = [year, journal.strip()] if journal else [year]
    parts = [p for p in parts if p]
    return " · ".join(parts)


def generate_entries(entries: list[dict], key_filter: str) -> str:
    items = []
    for entry in entries:
        title = sanitize_title(entry.get("title", "Untitled"))
        authors = format_authors(entry.get("author", ""))
        meta = build_meta(entry)
        anchor = entry.get("ID")
        if not anchor:
            anchor = entry.get("key") or ""
        if not anchor:
            continue
        items.append(
            ENTRY_TEMPLATE.format(key=anchor, title=title, authors=authors, meta=meta)
        )
    return "\n".join(items)


def sort_entries(entries: list[dict]) -> list[dict]:
    def sort_key(entry: dict):
        year = entry.get("year", "0")
        try:
            return -int(year)
        except ValueError:
            return 0

    return sorted(entries, key=sort_key)


def replace_block(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    pattern = re.compile(
        rf"({re.escape(start_marker)})(.*?){re.escape(end_marker)}",
        flags=re.S,
    )
    replacement_block = f"{start_marker}\n{replacement}\n{end_marker}"
    new_text, count = pattern.subn(replacement_block, text)
    if count == 0:
        raise RuntimeError(f"Markers not found for {start_marker} / {end_marker}")
    return new_text


def main() -> None:
    with open(BIB_FILE, encoding="utf-8") as bib_fp:
        bib_db = bibtexparser.load(bib_fp)

    journal_entries = [entry for entry in bib_db.entries if entry.get("ENTRYTYPE", "").lower() in JOURNAL_TYPES]
    conference_entries = [entry for entry in bib_db.entries if entry.get("ENTRYTYPE", "").lower() in CONFERENCE_TYPES]

    journal_entries = sort_entries(journal_entries)
    conference_entries = sort_entries(conference_entries)

    journal_block = generate_entries(journal_entries, "journal")
    conference_block = generate_entries(conference_entries, "conference")

    html_text = HTML_FILE.read_text(encoding="utf-8")
    html_text = replace_block(html_text, "<!-- BIBTEX_JOURNALS_START -->", "<!-- BIBTEX_JOURNALS_END -->", journal_block)
    html_text = replace_block(
        html_text,
        "<!-- BIBTEX_CONFERENCE_START -->",
        "<!-- BIBTEX_CONFERENCE_END -->",
        conference_block,
    )

    HTML_FILE.write_text(html_text, encoding="utf-8")
    print("Updated publications.html from citations.bib")


if __name__ == "__main__":
    main()
