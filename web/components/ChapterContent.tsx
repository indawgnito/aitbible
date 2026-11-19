"use client";

import { useState, useEffect } from "react";
import type { ParsedVerse, ParsedChapter } from "@/lib/data";
import { VerseModal } from "./VerseModal";

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
    </>
  );
}

interface VerseSpanProps {
  verse: ParsedVerse;
  onClick: () => void;
  isHighlighted?: boolean;
}

function VerseSpan({ verse, onClick, isHighlighted }: VerseSpanProps) {
  // Determine if we have notes or Greek (visual indicator)
  const hasExtras = verse.notes.length > 0 || verse.greek.length > 0;

  // Speaker segments get their color; everything else is plain text.
  const renderedSegments = (verse.segments ?? []).map((segment, index) => (
    <span
      key={index}
      className={
        segment.type === "speaker" && segment.speaker
          ? getSpeakerClass(segment.speaker)
          : ""
      }
    >
      {segment.content}
    </span>
  ));

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
        {renderedSegments}
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
