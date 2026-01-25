#!/usr/bin/env python3
"""
XML export module for the AIT Bible project.

Generates AIT XML format from translation files and Greek source data.
"""

import re
import html
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from greek_parser import GreekTextParser, Chapter as GreekChapter


@dataclass
class VerseNote:
    """A translation note for a specific term."""
    term: str
    explanation: str


@dataclass
class ParsedVerse:
    """A parsed verse with text, speaker tags, and notes."""
    verse_num: int
    text: str  # Raw text with speaker tags
    paragraph_start: bool
    notes: List[VerseNote]


@dataclass
class ParsedChapter:
    """A parsed chapter ready for XML export."""
    chapter_num: int
    verses: List[ParsedVerse]


# Speaker tag patterns
SPEAKER_PATTERNS = [
    (r'\[JESUS\](.*?)\[/JESUS\]', 'Jesus'),
    (r'\[GOD\](.*?)\[/GOD\]', 'God'),
    (r'\[ANGEL\](.*?)\[/ANGEL\]', 'angel'),
    (r'\[SCRIPTURE\](.*?)\[/SCRIPTURE\]', 'scripture'),
    (r'\[CROWD\](.*?)\[/CROWD\]', 'crowd'),
    (r'\[SPEAKER:([^\]]+)\](.*?)\[/SPEAKER\]', None),  # Named speaker
]


def escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return html.escape(text, quote=True)


def convert_speaker_tags(text: str) -> str:
    """Convert [SPEAKER] tags to <q who=""> XML elements."""
    result = text

    # Handle named speakers first (they have a different pattern)
    named_pattern = r'\[SPEAKER:([^\]]+)\](.*?)\[/SPEAKER\]'
    while True:
        match = re.search(named_pattern, result, re.DOTALL)
        if not match:
            break
        speaker = match.group(1).strip()
        content = match.group(2)
        # Escape the content but preserve any nested tags we already converted
        replacement = f'<q who="{escape_xml(speaker)}">{content}</q>'
        result = result[:match.start()] + replacement + result[match.end():]

    # Handle standard speaker tags
    for pattern, speaker in SPEAKER_PATTERNS:
        if speaker is None:
            continue  # Skip named speaker pattern, already handled
        while True:
            match = re.search(pattern, result, re.DOTALL)
            if not match:
                break
            content = match.group(1)
            replacement = f'<q who="{speaker}">{content}</q>'
            result = result[:match.start()] + replacement + result[match.end():]

    return result


def parse_notes_to_verses(notes_text: str) -> Dict[int, List[VerseNote]]:
    """
    Parse translation notes and attempt to associate them with verse numbers.

    Notes format: **"term" (v. N)**: explanation
    or: **"term" (vv. N-M)**: explanation
    or: **"term"**: explanation (no verse specified)

    Returns dict mapping verse_num -> list of notes for that verse.
    Notes without verse numbers are returned under key 0.
    """
    verse_notes: Dict[int, List[VerseNote]] = {}

    # Pattern to match note entries
    # Matches: **"term"** or **"term" (v. 5)** or **"term" (vv. 2-4)**
    note_pattern = re.compile(
        r'\*\*"([^"]+)"(?:\s*\(v+\.\s*(\d+)(?:-\d+)?\))?\*\*:\s*([^*]+?)(?=\*\*"|$)',
        re.DOTALL
    )

    for match in note_pattern.finditer(notes_text):
        term = match.group(1).strip()
        verse_str = match.group(2)
        explanation = match.group(3).strip()

        # Clean up explanation
        explanation = re.sub(r'\s+', ' ', explanation)

        verse_num = int(verse_str) if verse_str else 0

        note = VerseNote(term=term, explanation=explanation)

        if verse_num not in verse_notes:
            verse_notes[verse_num] = []
        verse_notes[verse_num].append(note)

    return verse_notes


def parse_translation_for_xml(filepath: Path) -> Optional[ParsedChapter]:
    """
    Parse a translation file for XML export.

    Preserves speaker tags and parses notes with verse associations.
    Handles speaker tags that span multiple verses.
    """
    content = filepath.read_text(encoding="utf-8")

    # Extract chapter number from filename or header
    chapter_match = re.search(r"chapter[_\s]+(\d+)", filepath.stem, re.IGNORECASE)
    if not chapter_match:
        header_match = re.search(r"#.*Chapter\s+(\d+)", content)
        if header_match:
            chapter_num = int(header_match.group(1))
        else:
            return None
    else:
        chapter_num = int(chapter_match.group(1))

    # Split into translation and notes
    parts = re.split(r"^---\s*$", content, maxsplit=1, flags=re.MULTILINE)
    translation_text = parts[0]
    notes_text = parts[1] if len(parts) > 1 else ""

    # Extract notes section
    notes_match = re.search(
        r"##\s*Translation Notes\s*\n(.*)",
        notes_text,
        re.DOTALL | re.IGNORECASE
    )
    notes_content = notes_match.group(1).strip() if notes_match else ""

    # Parse notes into verse associations
    verse_notes = parse_notes_to_verses(notes_content)

    # Parse verses
    verse_pattern = re.compile(r"\*\*(\d+)\*\*\s*")
    matches = list(verse_pattern.finditer(translation_text))

    verses = []

    # Track active speakers across verses
    active_speakers: List[str] = []

    for i, match in enumerate(matches):
        verse_num = int(match.group(1))
        start = match.end()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(translation_text)

        verse_text = translation_text[start:end].strip()

        # Check if this verse starts a new paragraph
        text_before = translation_text[:match.start()]
        paragraph_start = i == 0 or '\n\n' in text_before[-20:]

        # Clean up verse text but preserve speaker tags
        verse_text = re.sub(r"\n{2,}", " ", verse_text)
        verse_text = re.sub(r"\s+", " ", verse_text)
        verse_text = verse_text.strip()

        # Balance speaker tags for this verse
        verse_text, active_speakers = balance_speaker_tags(verse_text, active_speakers)

        # Get notes for this verse
        notes = verse_notes.get(verse_num, [])
        # Also include notes without verse numbers (key 0) in first verse only
        if verse_num == 1 and 0 in verse_notes:
            notes = verse_notes[0] + notes

        if verse_text:
            verses.append(ParsedVerse(
                verse_num=verse_num,
                text=verse_text,
                paragraph_start=paragraph_start,
                notes=notes
            ))

    return ParsedChapter(chapter_num=chapter_num, verses=verses)


def balance_speaker_tags(text: str, active_speakers: List[str]) -> Tuple[str, List[str]]:
    """
    Balance speaker tags within a verse, handling tags that span multiple verses.

    Args:
        text: The verse text
        active_speakers: List of currently active speaker tags from previous verses

    Returns:
        Tuple of (balanced text, updated active speakers list)
    """
    # Speaker tag patterns
    open_pattern = re.compile(r'\[(JESUS|GOD|ANGEL|SCRIPTURE|CROWD)\]')
    close_pattern = re.compile(r'\[/(JESUS|GOD|ANGEL|SCRIPTURE|CROWD)\]')
    named_open = re.compile(r'\[SPEAKER:([^\]]+)\]')
    named_close = re.compile(r'\[/SPEAKER\]')

    # Add opening tags for any active speakers at the start
    prefix = ""
    for speaker in active_speakers:
        if speaker.startswith("SPEAKER:"):
            prefix += f"[{speaker}]"
        else:
            prefix += f"[{speaker}]"

    # Find all opening and closing tags in this verse
    new_active = list(active_speakers)

    # Process standard tags
    for match in open_pattern.finditer(text):
        new_active.append(match.group(1))

    for match in close_pattern.finditer(text):
        speaker = match.group(1)
        if speaker in new_active:
            new_active.remove(speaker)

    # Process named speaker tags
    for match in named_open.finditer(text):
        new_active.append(f"SPEAKER:{match.group(1)}")

    for match in named_close.finditer(text):
        # Remove most recent SPEAKER: entry
        for i in range(len(new_active) - 1, -1, -1):
            if new_active[i].startswith("SPEAKER:"):
                new_active.pop(i)
                break

    # Add closing tags for any speakers still active at the end
    suffix = ""
    for speaker in reversed(new_active):
        if speaker.startswith("SPEAKER:"):
            suffix += "[/SPEAKER]"
        else:
            suffix += f"[/{speaker}]"

    balanced_text = prefix + text + suffix

    return balanced_text, new_active


def generate_verse_xml(
    verse: ParsedVerse,
    greek_words: List[Tuple[str, str]],
    indent: str = "      "
) -> str:
    """Generate XML for a single verse."""
    lines = []
    lines.append(f'{indent}<verse num="{verse.verse_num}">')

    # Text element with speaker tags converted
    text_content = verse.text
    # First escape XML special characters in the plain text portions
    # We need to be careful not to escape the speaker tags themselves

    # Convert speaker tags to XML elements
    text_with_xml = convert_speaker_tags(text_content)

    # Add paragraph marker if needed
    if verse.paragraph_start:
        text_with_xml = "<p/>" + text_with_xml

    lines.append(f'{indent}  <text>{text_with_xml}</text>')

    # Greek element with word lemmas
    if greek_words:
        lines.append(f'{indent}  <greek>')
        for word_text, lemma in greek_words:
            word_escaped = escape_xml(word_text)
            lemma_escaped = escape_xml(lemma)
            lines.append(f'{indent}    <w lemma="{lemma_escaped}">{word_escaped}</w>')
        lines.append(f'{indent}  </greek>')

    # Notes
    for note in verse.notes:
        term_escaped = escape_xml(note.term)
        explanation_escaped = escape_xml(note.explanation)
        lines.append(f'{indent}  <note term="{term_escaped}">{explanation_escaped}</note>')

    lines.append(f'{indent}</verse>')
    return '\n'.join(lines)


def generate_chapter_xml(
    chapter: ParsedChapter,
    greek_chapter: Optional[GreekChapter],
    indent: str = "    "
) -> str:
    """Generate XML for a single chapter."""
    lines = []
    lines.append(f'{indent}<chapter num="{chapter.chapter_num}">')

    # Get all Greek words for the chapter
    greek_words_by_verse = {}
    if greek_chapter:
        greek_words_by_verse = greek_chapter.get_all_verse_words()

    for verse in chapter.verses:
        greek_words = greek_words_by_verse.get(verse.verse_num, [])
        verse_xml = generate_verse_xml(verse, greek_words, indent + "  ")
        lines.append(verse_xml)

    lines.append(f'{indent}</chapter>')
    return '\n'.join(lines)


def export_book_to_xml(
    book_dir: Path,
    output_file: Path,
    book_id: str,
    book_name: str,
    greek_parser: Optional[GreekTextParser] = None
) -> None:
    """
    Export a book's translations to AIT XML format.

    Args:
        book_dir: Directory containing chapter translation files
        output_file: Path for the output XML file
        book_id: Lowercase book identifier (e.g., "matthew")
        book_name: Display name (e.g., "Matthew")
        greek_parser: Optional GreekTextParser for adding Greek word data
    """
    chapter_files = sorted(book_dir.glob("chapter_*.txt"))

    if not chapter_files:
        print(f"No chapter files found in {book_dir}")
        return

    output_file.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<ait version="1.0">',
        f'  <book id="{escape_xml(book_id)}" name="{escape_xml(book_name)}">',
    ]

    for chapter_file in chapter_files:
        chapter = parse_translation_for_xml(chapter_file)
        if not chapter:
            continue

        # Get Greek data if available
        greek_chapter = None
        if greek_parser:
            try:
                greek_chapter = greek_parser.get_chapter(book_id, chapter.chapter_num)
            except (ValueError, FileNotFoundError):
                pass

        chapter_xml = generate_chapter_xml(chapter, greek_chapter)
        lines.append(chapter_xml)

    lines.append('  </book>')
    lines.append('</ait>')

    output_file.write_text('\n'.join(lines), encoding='utf-8')
    print(f"Exported {len(chapter_files)} chapters to {output_file}")


def main():
    """CLI for XML export."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Export AIT Bible translations to XML format"
    )
    parser.add_argument(
        "book_dir",
        type=Path,
        help="Directory containing chapter translation files"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output XML file (default: ../web/data/<book>.xml)"
    )
    parser.add_argument(
        "--book-id",
        help="Book ID (default: directory name)"
    )
    parser.add_argument(
        "--book-name",
        help="Book display name (default: title-cased directory name)"
    )
    parser.add_argument(
        "--no-greek",
        action="store_true",
        help="Skip adding Greek word data"
    )
    parser.add_argument(
        "--greek-dir",
        type=Path,
        default=Path("greek_texts"),
        help="Directory containing Greek text files"
    )

    args = parser.parse_args()

    book_id = args.book_id or args.book_dir.name.lower()
    book_name = args.book_name or args.book_dir.name.title()
    output_file = args.output or Path("../web/data") / f"{book_id}.xml"

    greek_parser = None
    if not args.no_greek:
        greek_parser = GreekTextParser(str(args.greek_dir))

    export_book_to_xml(
        args.book_dir,
        output_file,
        book_id,
        book_name,
        greek_parser
    )


if __name__ == "__main__":
    main()
