#!/usr/bin/env python3
"""
Parse MorphGNT SBLGNT text files and extract Greek text by chapter/verse.

MorphGNT format (space-separated columns):
1. book/chapter/verse (e.g., "010101" = book 01, chapter 01, verse 01)
2. part of speech
3. parsing code
4. text (including punctuation)
5. word (punctuation stripped)
6. normalized word
7. lemma
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class GreekWord:
    """Represents a single Greek word with its morphological data."""
    book: int
    chapter: int
    verse: int
    part_of_speech: str
    parsing: str
    text: str  # includes punctuation
    word: str  # without punctuation
    normalized: str
    lemma: str

@dataclass
class Verse:
    """A single verse containing Greek words."""
    chapter: int
    verse_num: int
    words: List[GreekWord]
    
    @property
    def text(self) -> str:
        """Reconstruct the Greek text of this verse."""
        result = []
        for i, w in enumerate(self.words):
            # Add space before word unless it's the first word or previous ended with certain punctuation
            if i > 0:
                prev_text = self.words[i-1].text
                # Don't add space after opening punctuation or before closing punctuation
                if not prev_text.endswith(('(', '«', '—')) and not w.text.startswith((',', '.', '·', ';', ':', ')', '»', '—')):
                    result.append(' ')
            result.append(w.text)
        return "".join(result)

@dataclass 
class Chapter:
    """A chapter containing verses."""
    chapter_num: int
    verses: Dict[int, Verse]
    
    @property
    def text(self) -> str:
        """Reconstruct the Greek text of this chapter."""
        lines = []
        for verse_num in sorted(self.verses.keys()):
            verse = self.verses[verse_num]
            lines.append(f"{verse_num} {verse.text}")
        return "\n".join(lines)
    
    def get_verse_range(self, start: int, end: int) -> str:
        """Get Greek text for a range of verses."""
        lines = []
        for verse_num in range(start, end + 1):
            if verse_num in self.verses:
                verse = self.verses[verse_num]
                lines.append(f"{verse_num} {verse.text}")
        return "\n".join(lines)

class GreekTextParser:
    """Parse and access MorphGNT SBLGNT text files."""
    
    # Book name to MorphGNT file mapping
    BOOK_FILES = {
        "matthew": "61-Mt-morphgnt.txt",
        "mark": "62-Mk-morphgnt.txt",
        "luke": "63-Lk-morphgnt.txt",
        "john": "64-Jn-morphgnt.txt",
        "acts": "65-Ac-morphgnt.txt",
        "romans": "66-Ro-morphgnt.txt",
        "1corinthians": "67-1Co-morphgnt.txt",
        "2corinthians": "68-2Co-morphgnt.txt",
        "galatians": "69-Ga-morphgnt.txt",
        "ephesians": "70-Eph-morphgnt.txt",
        "philippians": "71-Php-morphgnt.txt",
        "colossians": "72-Col-morphgnt.txt",
        "1thessalonians": "73-1Th-morphgnt.txt",
        "2thessalonians": "74-2Th-morphgnt.txt",
        "1timothy": "75-1Ti-morphgnt.txt",
        "2timothy": "76-2Ti-morphgnt.txt",
        "titus": "77-Tit-morphgnt.txt",
        "philemon": "78-Phm-morphgnt.txt",
        "hebrews": "79-Heb-morphgnt.txt",
        "james": "80-Jas-morphgnt.txt",
        "1peter": "81-1Pe-morphgnt.txt",
        "2peter": "82-2Pe-morphgnt.txt",
        "1john": "83-1Jn-morphgnt.txt",
        "2john": "84-2Jn-morphgnt.txt",
        "3john": "85-3Jn-morphgnt.txt",
        "jude": "86-Jud-morphgnt.txt",
        "revelation": "87-Re-morphgnt.txt",
    }
    
    # Number of chapters per book
    CHAPTER_COUNTS = {
        "matthew": 28, "mark": 16, "luke": 24, "john": 21,
        "acts": 28, "romans": 16, "1corinthians": 16, "2corinthians": 13,
        "galatians": 6, "ephesians": 6, "philippians": 4, "colossians": 4,
        "1thessalonians": 5, "2thessalonians": 3, "1timothy": 6, "2timothy": 4,
        "titus": 3, "philemon": 1, "hebrews": 13, "james": 5,
        "1peter": 5, "2peter": 3, "1john": 5, "2john": 1, "3john": 1,
        "jude": 1, "revelation": 22,
    }
    
    def __init__(self, greek_texts_dir: str = "greek_texts"):
        self.greek_texts_dir = Path(greek_texts_dir)
        self._cache: Dict[str, Dict[int, Chapter]] = {}
    
    def _parse_line(self, line: str) -> Optional[GreekWord]:
        """Parse a single line from a MorphGNT file."""
        parts = line.strip().split()
        if len(parts) < 7:
            return None
        
        # Parse book/chapter/verse from first column (e.g., "010101")
        bcv = parts[0]
        book = int(bcv[0:2])
        chapter = int(bcv[2:4])
        verse = int(bcv[4:6])
        
        return GreekWord(
            book=book,
            chapter=chapter,
            verse=verse,
            part_of_speech=parts[1],
            parsing=parts[2],
            text=parts[3],
            word=parts[4],
            normalized=parts[5],
            lemma=parts[6],
        )
    
    def _load_book(self, book_name: str) -> Dict[int, Chapter]:
        """Load and parse a book's Greek text."""
        book_name = book_name.lower()
        
        if book_name in self._cache:
            return self._cache[book_name]
        
        if book_name not in self.BOOK_FILES:
            raise ValueError(f"Unknown book: {book_name}")
        
        filepath = self.greek_texts_dir / self.BOOK_FILES[book_name]
        
        if not filepath.exists():
            raise FileNotFoundError(
                f"Greek text file not found: {filepath}\n"
                f"Run 'python download_greek_texts.py' first."
            )
        
        # Parse all words
        chapters: Dict[int, Dict[int, List[GreekWord]]] = defaultdict(lambda: defaultdict(list))
        
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                word = self._parse_line(line)
                if word:
                    chapters[word.chapter][word.verse].append(word)
        
        # Build Chapter objects
        result: Dict[int, Chapter] = {}
        for chapter_num, verses_dict in chapters.items():
            verses = {
                verse_num: Verse(chapter_num, verse_num, words)
                for verse_num, words in verses_dict.items()
            }
            result[chapter_num] = Chapter(chapter_num, verses)
        
        self._cache[book_name] = result
        return result
    
    def get_chapter(self, book_name: str, chapter_num: int) -> Chapter:
        """Get a specific chapter from a book."""
        chapters = self._load_book(book_name)
        
        if chapter_num not in chapters:
            raise ValueError(f"Chapter {chapter_num} not found in {book_name}")
        
        return chapters[chapter_num]
    
    def get_chapter_text(self, book_name: str, chapter_num: int) -> str:
        """Get the Greek text of a chapter with verse numbers."""
        chapter = self.get_chapter(book_name, chapter_num)
        return chapter.text
    
    def get_verse_range_text(
        self, book_name: str, chapter_num: int, start_verse: int, end_verse: int
    ) -> str:
        """Get Greek text for a specific verse range."""
        chapter = self.get_chapter(book_name, chapter_num)
        return chapter.get_verse_range(start_verse, end_verse)
    
    def get_chapter_count(self, book_name: str) -> int:
        """Get the number of chapters in a book."""
        book_name = book_name.lower()
        if book_name not in self.CHAPTER_COUNTS:
            raise ValueError(f"Unknown book: {book_name}")
        return self.CHAPTER_COUNTS[book_name]
    
    def list_books(self) -> List[str]:
        """List all available books."""
        return list(self.BOOK_FILES.keys())


# Example usage
if __name__ == "__main__":
    parser = GreekTextParser()
    
    # Test with Matthew 6
    try:
        text = parser.get_verse_range_text("matthew", 6, 1, 9)
        print("Matthew 6:1-9 (Greek):")
        print(text)
    except FileNotFoundError as e:
        print(e)