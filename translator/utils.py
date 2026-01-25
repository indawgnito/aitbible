#!/usr/bin/env python3
"""
Utility scripts to process translations for the AIT Bible website.

- Combine chapter files into a single book file
- Export translations to JSON format for the Next.js app
- Export translations to AIT XML format
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from xml_export import export_book_to_xml
from greek_parser import GreekTextParser


@dataclass
class TranslatedVerse:
    """A single translated verse."""
    verse_num: int
    text: str
    paragraph_start: bool = False  # True if this verse starts a new paragraph


@dataclass
class TranslatedChapter:
    """A translated chapter with verses and notes."""
    chapter_num: int
    verses: List[TranslatedVerse]
    translation_notes: str


@dataclass
class TranslatedBook:
    """A complete translated book."""
    book_name: str
    chapters: List[TranslatedChapter]


def parse_translation_file(filepath: Path) -> Optional[TranslatedChapter]:
    """
    Parse a translation file into structured data.
    
    Expected format:
    - Verses marked with **N** where N is verse number
    - Translation notes after "## Translation Notes"
    """
    content = filepath.read_text(encoding="utf-8")
    
    # Extract chapter number from filename or header
    chapter_match = re.search(r"chapter[_\s]+(\d+)", filepath.stem, re.IGNORECASE)
    if not chapter_match:
        # Try header
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
    translation_notes = notes_match.group(1).strip() if notes_match else ""
    
    # Parse verses
    # Look for **N** patterns
    verse_pattern = re.compile(r"\*\*(\d+)\*\*\s*")
    
    verses = []
    
    # Find all verse markers
    matches = list(verse_pattern.finditer(translation_text))
    
    for i, match in enumerate(matches):
        verse_num = int(match.group(1))
        start = match.end()
        
        # End is either next verse or end of translation section
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            # End at notes section or end of content
            end = len(translation_text)
        
        verse_text = translation_text[start:end].strip()
        
        # Check if this verse starts a new paragraph
        # Look for double newline before this verse marker
        text_before_marker = translation_text[:match.start()]
        paragraph_start = i == 0 or text_before_marker.rstrip().endswith('\n\n') or '\n\n' in text_before_marker[-20:]
        
        # Clean up verse text (remove extra whitespace)
        verse_text = re.sub(r"\n{2,}", " ", verse_text)  # Collapse internal paragraph breaks
        verse_text = re.sub(r"\s+", " ", verse_text)  # Normalize whitespace
        verse_text = verse_text.strip()
        
        if verse_text:
            verses.append(TranslatedVerse(
                verse_num=verse_num, 
                text=verse_text,
                paragraph_start=paragraph_start
            ))
    
    return TranslatedChapter(
        chapter_num=chapter_num,
        verses=verses,
        translation_notes=translation_notes,
    )


def combine_book_chapters(book_dir: Path, output_file: Path) -> None:
    """
    Combine all chapter files in a directory into a single book file.
    """
    # Find all chapter files
    chapter_files = sorted(book_dir.glob("chapter_*.txt"))
    
    if not chapter_files:
        print(f"No chapter files found in {book_dir}")
        return
    
    book_name = book_dir.name.title()
    
    combined = [
        f"# {book_name}",
        f"# AIT Bible Translation",
        f"# aitbible.org",
        "",
        "=" * 60,
        "",
    ]
    
    for chapter_file in chapter_files:
        content = chapter_file.read_text(encoding="utf-8")
        
        # Remove file-level headers (lines starting with #)
        lines = content.split("\n")
        content_lines = []
        in_header = True
        for line in lines:
            if in_header and line.startswith("#"):
                continue
            if in_header and line.strip() == "":
                continue
            in_header = False
            content_lines.append(line)
        
        combined.append("\n".join(content_lines))
        combined.append("")
        combined.append("=" * 60)
        combined.append("")
    
    output_file.write_text("\n".join(combined), encoding="utf-8")
    print(f"Combined {len(chapter_files)} chapters into {output_file}")


def export_book_to_json(book_dir: Path, output_file: Path) -> None:
    """
    Export a book's translations to JSON format for the Next.js app.
    
    Output format:
    {
        "book": "Matthew",
        "chapters": [
            {
                "chapter": 1,
                "verses": [
                    {"verse": 1, "text": "...", "paragraphStart": true},
                    ...
                ],
                "notes": "..."
            },
            ...
        ]
    }
    """
    chapter_files = sorted(book_dir.glob("chapter_*.txt"))
    
    if not chapter_files:
        print(f"No chapter files found in {book_dir}")
        return
    
    # Create output directory if needed
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    book_name = book_dir.name.title()
    chapters_data = []
    
    for chapter_file in chapter_files:
        chapter = parse_translation_file(chapter_file)
        if chapter:
            chapter_data = {
                "chapter": chapter.chapter_num,
                "verses": [
                    {
                        "verse": v.verse_num, 
                        "text": v.text,
                        "paragraphStart": v.paragraph_start
                    }
                    for v in chapter.verses
                ],
                "notes": chapter.translation_notes,
            }
            chapters_data.append(chapter_data)
    
    output_data = {
        "book": book_name,
        "chapters": chapters_data,
    }
    
    output_file.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"Exported {len(chapters_data)} chapters to {output_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Process translation files for the AIT Bible website",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export single book to JSON
  python utils.py json output/matthew

  # Export all books to JSON
  python utils.py export-all output

  # Export single book to XML (with Greek word data)
  python utils.py xml output/matthew

  # Export all books to XML
  python utils.py export-all-xml output

  # Export XML without Greek data (faster)
  python utils.py xml output/matthew --no-greek

  # Export to custom location
  python utils.py json output/matthew -o ../website/data/matthew.json
  python utils.py xml output/matthew -o ../website/data/matthew.xml
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Combine command
    combine_parser = subparsers.add_parser(
        "combine",
        help="Combine chapter files into a single book file"
    )
    combine_parser.add_argument("book_dir", type=Path, help="Book directory")
    combine_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: <book_dir>_complete.txt)"
    )
    
    # Export JSON command
    json_parser = subparsers.add_parser(
        "json",
        help="Export book to JSON format"
    )
    json_parser.add_argument("book_dir", type=Path, help="Book directory")
    json_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: data/<book>.json)"
    )
    
    # Export all JSON command
    all_parser = subparsers.add_parser(
        "export-all",
        help="Export all books in output/ to JSON"
    )
    all_parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory containing book folders (e.g., 'output')"
    )
    all_parser.add_argument(
        "-o", "--json-dir",
        type=Path,
        help="JSON output directory (default: ./data)"
    )

    # Export XML command
    xml_parser = subparsers.add_parser(
        "xml",
        help="Export book to AIT XML format (with Greek and speaker tags)"
    )
    xml_parser.add_argument("book_dir", type=Path, help="Book directory")
    xml_parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: ../web/data/<book>.xml)"
    )
    xml_parser.add_argument(
        "--no-greek",
        action="store_true",
        help="Skip adding Greek word data"
    )

    # Export all XML command
    all_xml_parser = subparsers.add_parser(
        "export-all-xml",
        help="Export all books in output/ to AIT XML format"
    )
    all_xml_parser.add_argument(
        "output_dir",
        type=Path,
        help="Directory containing book folders (e.g., 'output')"
    )
    all_xml_parser.add_argument(
        "-o", "--xml-dir",
        type=Path,
        help="XML output directory (default: ../web/data)"
    )
    all_xml_parser.add_argument(
        "--no-greek",
        action="store_true",
        help="Skip adding Greek word data"
    )

    args = parser.parse_args()
    
    if args.command == "combine":
        output_file = args.output or args.book_dir.with_suffix("_complete.txt")
        combine_book_chapters(args.book_dir, output_file)
    
    elif args.command == "json":
        output_file = args.output or Path("data") / f"{args.book_dir.name}.json"
        export_book_to_json(args.book_dir, output_file)
    
    elif args.command == "export-all":
        json_dir = args.json_dir or Path("data")
        json_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for book_dir in args.output_dir.iterdir():
            if book_dir.is_dir() and book_dir.name != "json":
                output_file = json_dir / f"{book_dir.name}.json"
                export_book_to_json(book_dir, output_file)
                count += 1

        print(f"\nExported {count} books to {json_dir}/")

    elif args.command == "xml":
        book_id = args.book_dir.name.lower()
        book_name = args.book_dir.name.title()
        output_file = args.output or Path("../web/data") / f"{book_id}.xml"

        greek_parser = None
        if not args.no_greek:
            greek_parser = GreekTextParser("greek_texts")

        export_book_to_xml(
            args.book_dir,
            output_file,
            book_id,
            book_name,
            greek_parser
        )

    elif args.command == "export-all-xml":
        xml_dir = args.xml_dir or Path("../web/data")
        xml_dir.mkdir(parents=True, exist_ok=True)

        greek_parser = None
        if not args.no_greek:
            greek_parser = GreekTextParser("greek_texts")

        count = 0
        for book_dir in args.output_dir.iterdir():
            if book_dir.is_dir() and book_dir.name not in ("json", "xml"):
                book_id = book_dir.name.lower()
                book_name = book_dir.name.title()
                output_file = xml_dir / f"{book_id}.xml"
                export_book_to_xml(
                    book_dir,
                    output_file,
                    book_id,
                    book_name,
                    greek_parser
                )
                count += 1

        print(f"\nExported {count} books to {xml_dir}/")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()