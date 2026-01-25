"use client";

import { useState, useEffect } from "react";
import type { ParsedVerse, ParsedChapter } from "@/lib/data";
import { VerseModal } from "./VerseModal";
import { WordModal } from "./WordModal";
import { matchGlossaryTerm, type GlossaryTerm } from "@/lib/glossary";

interface ChapterContentProps {
  chapter: ParsedChapter;
  bookName: string;
  chapterNum: number;
  kjvVerses?: Record<number, string>;
}

export function ChapterContent({
  chapter,
  bookName,
  chapterNum,
  kjvVerses = {},
}: ChapterContentProps) {
  const [selectedVerse, setSelectedVerse] = useState<ParsedVerse | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [highlightedVerse, setHighlightedVerse] = useState<number | null>(null);
  const [selectedTerm, setSelectedTerm] = useState<GlossaryTerm | null>(null);
  const [isWordModalOpen, setIsWordModalOpen] = useState(false);

  // Handle deep linking via URL hash (e.g., /matthew/5#3)
  useEffect(() => {
    const handleHash = () => {
      const hash = window.location.hash.slice(1); // Remove the #
      const verseNum = parseInt(hash, 10);

      if (!isNaN(verseNum) && verseNum > 0) {
        // Scroll to the verse
        const element = document.getElementById(`v${verseNum}`);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "center" });
          setHighlightedVerse(verseNum);

          // Remove highlight after 3 seconds
          setTimeout(() => setHighlightedVerse(null), 3000);
        }
      }
    };

    // Check hash on mount
    handleHash();

    // Listen for hash changes
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);

  const handleVerseClick = (verse: ParsedVerse) => {
    setSelectedVerse(verse);
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedVerse(null);
  };

  const handleTermClick = (term: GlossaryTerm) => {
    setSelectedTerm(term);
    setIsWordModalOpen(true);
  };

  const handleCloseWordModal = () => {
    setIsWordModalOpen(false);
    setSelectedTerm(null);
  };

  // Group verses into paragraphs
  const paragraphs: ParsedVerse[][] = [];
  let currentParagraph: ParsedVerse[] = [];

  chapter.verses.forEach((verse) => {
    if (verse.paragraphStart && currentParagraph.length > 0) {
      paragraphs.push(currentParagraph);
      currentParagraph = [];
    }
    currentParagraph.push(verse);
  });
  if (currentParagraph.length > 0) {
    paragraphs.push(currentParagraph);
  }

  return (
    <>
      <div className="prose-reading">
        {paragraphs.map((paragraph, pIndex) => (
          <p key={pIndex} className="mb-4">
            {paragraph.map((verse) => (
              <VerseSpan
                key={verse.verse}
                verse={verse}
                onClick={() => handleVerseClick(verse)}
                onTermClick={handleTermClick}
                isHighlighted={highlightedVerse === verse.verse}
              />
            ))}
          </p>
        ))}
      </div>

      <VerseModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        verse={selectedVerse}
        bookName={bookName}
        chapterNum={chapterNum}
        kjvText={selectedVerse ? kjvVerses[selectedVerse.verse] : undefined}
      />

      <WordModal
        isOpen={isWordModalOpen}
        onClose={handleCloseWordModal}
        term={selectedTerm}
      />
    </>
  );
}

interface VerseSpanProps {
  verse: ParsedVerse;
  onClick: () => void;
  onTermClick: (term: GlossaryTerm) => void;
  isHighlighted?: boolean;
}

function VerseSpan({ verse, onClick, onTermClick, isHighlighted }: VerseSpanProps) {
  // Determine if we have notes or Greek (visual indicator)
  const hasExtras = verse.notes.length > 0 || verse.greek.length > 0;

  // Render segments with proper speaker coloring and glossary term detection
  const renderedSegments = renderSegments(verse.segments, onTermClick);

  // We need to insert the verse number before the first character
  // Split the first segment to wrap verse number with first word
  const firstSegment = renderedSegments[0];
  const restSegments = renderedSegments.slice(1);

  return (
    <>
      <span
        id={`v${verse.verse}`}
        className={`transition-colors duration-500 rounded px-1 -mx-1 ${
          isHighlighted
            ? "bg-neutral-200 dark:bg-neutral-700"
            : "bg-transparent"
        }`}
      >
        <span className="verse-wrapper">
          <sup
            className={`verse-num cursor-pointer hover:text-amber-900 dark:hover:text-amber-400 ${
              hasExtras ? "underline decoration-dotted" : ""
            }`}
            onClick={onClick}
            title="Click to see Greek text and notes"
          >
            {verse.verse}
          </sup>
        </span>
        {firstSegment}
        {restSegments}
      </span>
      {" "}
    </>
  );
}

/**
 * Get the appropriate CSS class for a speaker.
 * Only Jesus (red), God (purple), and angels (blue) get special colors.
 */
function getSpeakerClass(speaker: string): string {
  switch (speaker.toLowerCase()) {
    case "jesus":
      return "text-red-700 dark:text-red-500";
    case "god":
      return "text-purple-700 dark:text-purple-400";
    case "angel":
      return "text-blue-700 dark:text-blue-400";
    default:
      return ""; // Normal text for all other speakers
  }
}

/**
 * Render text segments with proper speaker coloring and glossary term detection.
 * Only the actual quoted words get colored, not the surrounding narrative.
 */
function renderSegments(
  segments: { type: "text" | "speaker"; content: string; speaker?: string }[] | undefined,
  onTermClick: (term: GlossaryTerm) => void
): React.ReactNode[] {
  if (!segments || segments.length === 0) {
    return [];
  }

  return segments.map((segment, index) => {
    const speakerClass = segment.type === "speaker" && segment.speaker
      ? getSpeakerClass(segment.speaker)
      : "";

    // Render the content with glossary term detection
    const contentWithTerms = renderTextWithGlossaryTerms(
      segment.content,
      onTermClick,
      speakerClass
    );

    return <span key={index}>{contentWithTerms}</span>;
  });
}

/**
 * Render text with glossary terms wrapped in clickable spans.
 */
function renderTextWithGlossaryTerms(
  text: string,
  onTermClick: (term: GlossaryTerm) => void,
  speakerClass: string
): React.ReactNode[] {
  const result: React.ReactNode[] = [];
  let currentIndex = 0;
  let keyIndex = 0;

  while (currentIndex < text.length) {
    // Try to match a glossary term at current position
    const match = matchGlossaryTerm(text, currentIndex);

    if (match) {
      // Add any text before the match
      if (currentIndex < text.indexOf(match.matchedText, currentIndex)) {
        const beforeText = text.slice(
          currentIndex,
          text.indexOf(match.matchedText, currentIndex)
        );
        result.push(
          <span key={keyIndex++} className={speakerClass}>
            {beforeText}
          </span>
        );
      }

      // Add the glossary term as a clickable element
      result.push(
        <span
          key={keyIndex++}
          className={`glossary-term cursor-pointer ${speakerClass}`}
          onClick={(e) => {
            e.stopPropagation();
            onTermClick(match.term);
          }}
          title={match.term.brief}
        >
          {match.matchedText}
        </span>
      );

      currentIndex =
        text.indexOf(match.matchedText, currentIndex) + match.matchedText.length;
    } else {
      // No match, find the next word boundary or end
      const nextSpace = text.indexOf(" ", currentIndex + 1);
      const endIndex = nextSpace === -1 ? text.length : nextSpace + 1;

      result.push(
        <span key={keyIndex++} className={speakerClass}>
          {text.slice(currentIndex, endIndex)}
        </span>
      );

      currentIndex = endIndex;
    }
  }

  return result;
}
