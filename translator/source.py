#!/usr/bin/env python3
"""
Source ground truth for the AIT pipeline.

Everything about *which verses exist* and *which Greek words they contain*
comes from MorphGNT (SBLGNT), never from the model. The translator fills
this inventory; it cannot add, merge or drop a verse.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from greek_parser import GreekTextParser

DEFAULT_GREEK_DIR = Path(__file__).parent / "greek_texts"

# SBLGNT apparatus sigla that mark variation units. They are editorial
# markup, not text, so they are stripped before the Greek reaches the model.
_SIGLA = re.compile(r"[⸀⸁⸂⸃⸄⸅]")
_BRACKETS = re.compile(r"[\[\]⟦⟧]")
_PUNCT = re.compile(r"[.,;·:()—]")

BOOKS: List[str] = list(GreekTextParser.BOOK_FILES.keys())


@dataclass
class SourceWord:
    text: str   # surface form, sigla removed; SBLGNT brackets and punctuation kept
    lemma: str


@dataclass
class SourceVerse:
    book: str
    chapter: int
    verse: int
    words: List[SourceWord] = field(default_factory=list)
    # "double": wholly inside ⟦ ⟧ — SBLGNT prints it but judges it not original.
    # "partial-double": only part of the verse is inside ⟦ ⟧ (Mark 16:8).
    # "single": contains [ ] — SBLGNT judges the words doubtful.
    # "": undisputed.
    # The bracket characters stay in the Greek so the translator can carry
    # them into the English at the matching place.
    bracket: str = ""

    @property
    def ref(self) -> str:
        return f"{self.book} {self.chapter}:{self.verse}"

    @property
    def greek(self) -> str:
        return " ".join(w.text for w in self.words)

    @property
    def lemmas(self) -> List[str]:
        return [w.lemma for w in self.words]


class Source:
    """Verse inventory with lemmas for the whole New Testament."""

    def __init__(self, greek_dir: Path = DEFAULT_GREEK_DIR):
        self._parser = GreekTextParser(str(greek_dir))
        self._books: Dict[str, Dict[int, Dict[int, SourceVerse]]] = {}

    def _load(self, book: str) -> Dict[int, Dict[int, SourceVerse]]:
        book = book.lower()
        if book in self._books:
            return self._books[book]
        chapters = self._parser._load_book(book)
        out: Dict[int, Dict[int, SourceVerse]] = {}
        in_double = False
        for c in sorted(chapters):
            out[c] = {}
            for v in sorted(chapters[c].verses):
                sv = SourceVerse(book, c, v)
                inside = outside = 0
                saw_single = False
                for w in chapters[c].verses[v].words:
                    raw = w.text
                    if "⟦" in raw:
                        in_double = True
                    if "[" in raw or "]" in raw:
                        saw_single = True
                    if in_double:
                        inside += 1
                    else:
                        outside += 1
                    sv.words.append(SourceWord(_SIGLA.sub("", raw), w.lemma))
                    if "⟧" in raw:
                        in_double = False
                if inside and not outside:
                    sv.bracket = "double"
                elif inside:
                    sv.bracket = "partial-double"
                elif saw_single:
                    sv.bracket = "single"
                out[c][v] = sv
        self._books[book] = out
        return out

    def chapters(self, book: str) -> List[int]:
        return sorted(self._load(book))

    def chapter(self, book: str, chapter: int) -> List[SourceVerse]:
        ch = self._load(book)[chapter]
        return [ch[v] for v in sorted(ch)]

    def all_chapters(self) -> List[Tuple[str, int]]:
        return [(b, c) for b in BOOKS for c in self.chapters(b)]

    def all_verses(self) -> List[SourceVerse]:
        return [v for b, c in self.all_chapters() for v in self.chapter(b, c)]

    def verse_keys(self) -> set:
        return {(v.book, v.chapter, v.verse) for v in self.all_verses()}


def bare(word: str) -> str:
    """Surface form without punctuation, for display in concordances."""
    return _PUNCT.sub("", _BRACKETS.sub("", word))


if __name__ == "__main__":
    src = Source()
    verses = src.all_verses()
    print(f"{len(BOOKS)} books, {len(src.all_chapters())} chapters, "
          f"{len(verses)} verses, {sum(len(v.words) for v in verses)} words")
    for kind in ("double", "partial-double", "single"):
        refs = [v.ref for v in verses if v.bracket == kind]
        print(f"{kind}-bracketed verses ({len(refs)}): {', '.join(refs)}")
