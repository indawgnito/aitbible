"use client";

import { useState } from "react";

interface TranslationNotesProps {
  notes: string;
}

export function TranslationNotes({ notes }: TranslationNotesProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!notes || notes.trim() === "") {
    return null;
  }

  // Parse the notes markdown-style into structured sections
  const parseNotes = (text: string) => {
    const sections: { term: string; explanation: string }[] = [];

    // Split on the pattern **"term"** or **"term" (verse)**:
    // This splits the text at each note heading
    const parts = text.split(/\*\*"([^"]+)"(?:\s*\([^)]+\))?\*\*:\s*/);

    // parts[0] is any text before the first term (usually empty)
    // parts[1] is the first term, parts[2] is its explanation
    // parts[3] is the second term, parts[4] is its explanation, etc.

    for (let i = 1; i < parts.length; i += 2) {
      const term = parts[i];
      const explanation = parts[i + 1]?.trim() || "";
      if (term && explanation) {
        sections.push({ term, explanation });
      }
    }

    return sections;
  };

  // Render text with *italics* converted to <em> tags
  const renderWithItalics = (text: string) => {
    const parts = text.split(/\*([^*]+)\*/g);
    return parts.map((part, index) => {
      // Odd indices are the italicized parts
      if (index % 2 === 1) {
        return <em key={index}>{part}</em>;
      }
      return part;
    });
  };

  const parsedNotes = parseNotes(notes);

  return (
    <div className="mt-12 border-t border-neutral-200 dark:border-neutral-800 pt-8">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors font-sans"
      >
        <svg
          className={`w-4 h-4 transition-transform ${
            isOpen ? "rotate-90" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
        <span className="text-sm font-medium uppercase tracking-wide">
          Translation Notes
        </span>
      </button>

      {isOpen && (
        <div className="mt-6 space-y-6">
          {parsedNotes.length > 0 ? (
            parsedNotes.map((note, index) => (
              <div key={index} className="group">
                <h4 className="font-sans font-semibold text-amber-700 dark:text-amber-500 mb-1">
                  &quot;{note.term}&quot;
                </h4>
                <p className="text-base text-neutral-700 dark:text-neutral-300 leading-relaxed">
                  {renderWithItalics(note.explanation)}
                </p>
              </div>
            ))
          ) : (
            // Fallback: just render the raw notes if parsing didn't work
            <div className="text-base text-neutral-700 dark:text-neutral-300 leading-relaxed whitespace-pre-wrap">
              {notes}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
