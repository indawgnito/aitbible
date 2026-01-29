#!/usr/bin/env python3
"""
Build greekAppearsIn data for glossary terms.

For each glossary term, scans all XML files to find verses where the Greek lemma
appears but the English AIT rendering does NOT appear in the verse text.
This produces the "same Greek word, different English" references.

Usage:
    python3 translator/build_greek_refs.py
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "web" / "data"
GLOSSARY_PATH = DATA_DIR / "glossary.json"


def parse_xml_files():
    """Parse all XML files and return a structure of book -> chapter -> verse -> {lemmas, text}."""
    all_data = {}

    for xml_file in sorted(DATA_DIR.glob("*.xml")):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        book_el = root.find("book")
        if book_el is None:
            continue

        book_id = book_el.get("id")
        all_data[book_id] = {}

        for chapter_el in book_el.findall("chapter"):
            chapter_num = int(chapter_el.get("num"))
            all_data[book_id][chapter_num] = {}

            for verse_el in chapter_el.findall("verse"):
                verse_num = int(verse_el.get("num"))

                # Extract lemmas from <greek><w lemma="..."> elements
                lemmas = set()
                greek_el = verse_el.find("greek")
                if greek_el is not None:
                    for w_el in greek_el.findall("w"):
                        lemma = w_el.get("lemma", "").strip()
                        if lemma:
                            lemmas.add(lemma.lower())

                # Extract English text (flatten all text content in <text>)
                text_el = verse_el.find("text")
                english_text = ""
                if text_el is not None:
                    english_text = "".join(text_el.itertext()).strip()

                all_data[book_id][chapter_num][verse_num] = {
                    "lemmas": lemmas,
                    "text": english_text,
                }

    return all_data


def make_appears_in_set(appears_in):
    """Convert appearsIn list to a set of (book, chapter, verse) tuples."""
    result = set()
    for ref in appears_in:
        for v in ref["verses"]:
            result.add((ref["book"], ref["chapter"], v))
    return result


def find_greek_refs(term, all_data):
    """Find verses where the Greek lemma appears but the English rendering does not."""
    lemma = term["lemma"].strip().lower()
    # Handle compound lemmas like "ζωή, αἰώνιος" or "ζωή/αἰώνιος"
    lemma_parts = [p.strip() for p in re.split(r"[,/\s]+", lemma) if p.strip()]

    if not lemma_parts:
        return []

    # Build set of existing appearsIn refs
    existing_refs = make_appears_in_set(term["appearsIn"])

    # Build the AIT rendering pattern for matching against English text
    rendering = term["aitRendering"].lower()

    # Collect matching verses grouped by book+chapter
    matches = {}  # (book, chapter) -> [verse_nums]

    for book_id, chapters in all_data.items():
        for chapter_num, verses in chapters.items():
            for verse_num, verse_data in verses.items():
                # Check if any lemma part is in this verse's lemmas
                has_lemma = any(
                    part in verse_data["lemmas"] for part in lemma_parts
                )
                if not has_lemma:
                    continue

                # Skip if this verse is already in appearsIn
                if (book_id, chapter_num, verse_num) in existing_refs:
                    continue

                # Check that the English rendering does NOT appear in the text
                text_lower = verse_data["text"].lower()
                if rendering in text_lower:
                    # The English rendering IS present, so this is a regular match
                    # (should be in appearsIn, not greekAppearsIn)
                    continue

                key = (book_id, chapter_num)
                if key not in matches:
                    matches[key] = []
                matches[key].append(verse_num)

    # Convert to the same format as appearsIn
    result = []
    for (book_id, chapter_num), verse_nums in sorted(matches.items()):
        result.append({
            "book": book_id,
            "chapter": chapter_num,
            "verses": sorted(verse_nums),
        })

    return result


def main():
    print("Loading glossary...")
    with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
        glossary = json.load(f)

    print("Parsing XML files...")
    all_data = parse_xml_files()
    print(f"  Parsed {len(all_data)} books")

    total_new_refs = 0
    terms_with_refs = 0

    for term in glossary["terms"]:
        greek_refs = find_greek_refs(term, all_data)
        term["greekAppearsIn"] = greek_refs

        ref_count = sum(len(r["verses"]) for r in greek_refs)
        if ref_count > 0:
            terms_with_refs += 1
            total_new_refs += ref_count

        if ref_count > 0:
            appears_count = sum(len(r["verses"]) for r in term["appearsIn"])
            print(f"  {term['aitRendering']}: appearsIn={appears_count}, greekAppearsIn={ref_count}")

    print(f"\nTotal: {terms_with_refs} terms with Greek refs, {total_new_refs} new references")

    print("Writing updated glossary.json...")
    with open(GLOSSARY_PATH, "w", encoding="utf-8") as f:
        json.dump(glossary, f, ensure_ascii=False, indent=2)

    print("Done!")


if __name__ == "__main__":
    main()
