#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("pdfplumber no está instalado. Instálalo con: pip install pdfplumber")
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent
PDF_PATH = ROOT / "BKLN_Base_de_Conocimiento_Asistente_Web.pdf"
OUTPUT_PATH = ROOT / "knowledge.json"
SOURCE_URL = "https://www.bklnsoftware.tech"

HEADER_FOOTER_BLOCKLIST = {
    "bkln software & systems",
    "bkln software",
    "bkln",
    "base de conocimiento",
    "base de conocimiento del asistente web",
    "bkln software & systems - base de conocimiento",
}


def normalize_text(raw_text: str) -> str:
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    replacements = [
        ("hello@bklnsoftware.com", "hello@bklnsoftware.tech"),
        ("bklnsoftware.com", "bklnsoftware.tech"),
        ("bklsoftware.tech", "bklnsoftware.tech"),
        ("bklnmarketplace.com", "bklnmarketplace.com"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    text = text.replace("https://www.bklnsoftware.com", "https://www.bklnsoftware.tech")
    text = text.replace("http://www.bklnsoftware.com", "https://www.bklnsoftware.tech")

    cleaned_lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            continue
        normalized = line.lower()
        if normalized in HEADER_FOOTER_BLOCKLIST:
            continue
        if re.fullmatch(r"(página|page)\s+\d+.*", normalized):
            continue
        if re.fullmatch(r"\d+\s*de\s*\d+", normalized):
            continue
        cleaned_lines.append(line)

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_sections(text: str):
    heading_pattern = re.compile(
        r"(?m)^\s*(\d+(?:\.\d+)*)\s*(?:[.):]\s*)?\s*([A-ZÁÉÍÓÚÑ0-9&/][^\n]{0,140})\s*$"
    )
    matches = list(heading_pattern.finditer(text))
    sections = []

    for index, match in enumerate(matches):
        section_number = match.group(1).strip()
        section_title = match.group(2).strip()

        if section_number == "1" and "instrucciones" in section_title.lower():
            continue

        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end]
        content = content[match.end() - start :].strip()
        if not content:
            continue

        sections.append(
            {
                "section": f"{section_number}. {section_title}",
                "title": section_title,
                "content": normalize_text(content),
            }
        )

    return sections


def split_long_paragraph(paragraph: str, max_chars: int = 1200):
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    fragments = []
    current = ""

    for sentence in sentences:
        candidate = f"{current} {sentence}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue

        if current.strip():
            fragments.append(current.strip())
        current = sentence

    if current.strip():
        fragments.append(current.strip())

    return fragments


def chunk_section(content: str, max_chars: int = 1200, min_chars: int = 200):
    paragraphs = []
    for block in re.split(r"\n\s*\n+", content):
        cleaned = re.sub(r"\s+", " ", block).strip()
        if cleaned:
            paragraphs.append(cleaned)

    fragments = []
    current = ""

    for paragraph in paragraphs:
        if not paragraph:
            continue

        if len(paragraph) <= max_chars:
            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
            if len(candidate) <= max_chars:
                current = candidate
                continue

        if current.strip():
            fragments.append(current.strip())
            current = ""

        if len(paragraph) <= max_chars:
            current = paragraph
        else:
            for sub_fragment in split_long_paragraph(paragraph, max_chars=max_chars):
                fragments.append(sub_fragment)

    if current.strip():
        fragments.append(current.strip())

    merged = []
    for fragment in fragments:
        if not fragment:
            continue
        if not merged:
            merged.append(fragment)
            continue

        if len(merged[-1]) < min_chars and len(merged[-1]) + len(fragment) <= max_chars:
            merged[-1] = f"{merged[-1]} {fragment}".strip()
        else:
            merged.append(fragment)

    final = []
    for fragment in merged:
        if len(fragment) < min_chars and final:
            final[-1] = f"{final[-1]} {fragment}".strip()
        else:
            final.append(fragment)

    final = [fragment.strip() for fragment in final if fragment.strip()]
    return final


def build_knowledge_entries():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"No se encontró el PDF: {PDF_PATH}")

    pdf = pdfplumber.open(PDF_PATH)
    pages_text = []
    for page in pdf.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
    pdf.close()

    full_text = "\n\n".join(pages_text)
    cleaned = normalize_text(full_text)
    sections = split_sections(cleaned)

    entries = []
    for section in sections:
        fragments = chunk_section(section["content"])
        if not fragments:
            continue

        if len(fragments) == 1:
            title = f"{section['title']} — ficha rápida"
        else:
            title = section["title"]

        for order, fragment in enumerate(fragments, start=1):
            fragment_title = title
            if len(fragments) > 1:
                fragment_title = f"{title} — fragmento {order}"

            entries.append(
                {
                    "title": fragment_title,
                    "content": fragment,
                    "source_url": SOURCE_URL,
                    "section": section["section"],
                }
            )

    return entries


def main():
    try:
        entries = build_knowledge_entries()
    except FileNotFoundError as exc:
        print(str(exc))
        raise SystemExit(1)

    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(entries, fh, ensure_ascii=False, indent=2)

    avg_length = round(sum(len(item["content"]) for item in entries) / len(entries), 1) if entries else 0
    sections = sorted({item["section"] for item in entries})

    print(f"Fragmentos generados: {len(entries)}")
    print(f"Longitud media: {avg_length} caracteres")
    print(f"Secciones cubiertas: {len(sections)}")
    print("- " + "\n- ".join(sections[:10]))


if __name__ == "__main__":
    main()
