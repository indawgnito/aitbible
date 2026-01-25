"use client";

import { useEffect, useCallback, useState } from "react";
import type { ParsedVerse } from "@/lib/data";

type ViewMode = "compare" | "greek";

interface VerseModalProps {
  isOpen: boolean;
  onClose: () => void;
  verse: ParsedVerse | null;
  bookName: string;
  chapterNum: number;
  kjvText?: string;
}

export function VerseModal({
  isOpen,
  onClose,
  verse,
  bookName,
  chapterNum,
  kjvText,
}: VerseModalProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("compare");
  const [copied, setCopied] = useState(false);
  const [copyTimeout, setCopyTimeout] = useState<NodeJS.Timeout | null>(null);

  // Handle escape key
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose]
  );

  useEffect(() => {
    if (isOpen) {
      document.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen, handleKeyDown]);

  if (!isOpen || !verse) return null;

  const reference = `${bookName} ${chapterNum}:${verse.verse}`;

  const handleCopy = async () => {
    const textToCopy = `${verse.text}\n\n- ${reference} (AIT Bible)`;
    try {
      await navigator.clipboard.writeText(textToCopy);
      if (copyTimeout) clearTimeout(copyTimeout);
      setCopied(true);
      const timeout = setTimeout(() => setCopied(false), 2000);
      setCopyTimeout(timeout);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative w-full sm:max-w-lg max-h-[85vh] overflow-y-auto bg-white dark:bg-neutral-900 sm:rounded-xl rounded-t-xl shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold font-sans text-neutral-900 dark:text-neutral-100">
            {reference}
          </h2>
          <button
            onClick={onClose}
            className="p-2 -m-2 text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors cursor-pointer"
            aria-label="Close"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-6">
          {/* View Toggle */}
          <div className="flex gap-1 p-1 bg-neutral-100 dark:bg-neutral-800 rounded-lg font-sans">
            <button
              onClick={() => setViewMode("compare")}
              className={`flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors cursor-pointer ${
                viewMode === "compare"
                  ? "bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 shadow-sm"
                  : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200"
              }`}
            >
              KJV
            </button>
            <button
              onClick={() => setViewMode("greek")}
              className={`flex-1 px-3 py-1.5 text-sm font-medium rounded-md transition-colors cursor-pointer ${
                viewMode === "greek"
                  ? "bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100 shadow-sm"
                  : "text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-200"
              }`}
            >
              Greek
            </button>
          </div>

          {/* AIT Translation - always visible */}
          <section>
            <h3 className="text-xs font-sans font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-2">
              AIT Translation
            </h3>
            <p className="text-lg leading-relaxed text-neutral-800 dark:text-neutral-200">
              {renderVerseText(verse)}
            </p>
          </section>

          {/* Compare Mode: KJV */}
          {viewMode === "compare" && kjvText && (
            <section>
              <h3 className="text-xs font-sans font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-2">
                King James Version
              </h3>
              <p className="text-lg leading-relaxed text-neutral-800 dark:text-neutral-200 italic">
                {kjvText}
              </p>
            </section>
          )}

          {/* Greek Mode: Greek Text */}
          {viewMode === "greek" && verse.greek.length > 0 && (
            <section>
              <h3 className="text-xs font-sans font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-3">
                Greek (SBLGNT)
              </h3>
              <div className="flex flex-wrap gap-x-3 gap-y-2">
                {verse.greek.map((word, idx) => (
                  <div key={idx} className="text-center">
                    <div className="text-lg text-neutral-900 dark:text-neutral-100">
                      {word.text}
                    </div>
                    <div className="text-xs text-neutral-500 dark:text-neutral-400 font-sans">
                      {word.lemma}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Translation Notes - always visible if present */}
          {verse.notes.length > 0 && (
            <section>
              <h3 className="text-xs font-sans font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-3">
                Translation Notes
              </h3>
              <div className="space-y-3">
                {verse.notes.map((note, idx) => (
                  <div key={idx}>
                    <span className="font-semibold text-amber-700 dark:text-amber-500">
                      &quot;{note.term}&quot;
                    </span>
                    <span className="text-neutral-700 dark:text-neutral-300">
                      {" "}
                      &mdash; {note.explanation}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-neutral-900 border-t border-neutral-200 dark:border-neutral-800 px-6 py-4 flex gap-3">
          <button
            onClick={handleCopy}
            className={`btn flex-1 flex items-center justify-center gap-2 font-sans text-sm ${
              copied
                ? "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300"
                : "btn-secondary"
            }`}
          >
            {copied ? (
              <>
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Copied!
              </>
            ) : (
              <>
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                Copy
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

/**
 * Render verse text with speaker highlighting.
 */
function renderVerseText(verse: ParsedVerse): React.ReactNode {
  // If no segments or no speaker, just return plain text
  if (!verse.segments || verse.segments.length === 0 || !verse.hasSpeaker) {
    return verse.text;
  }

  // Render segments with speaker styling
  return verse.segments.map((segment, idx) => {
    if (segment.type === "speaker" && segment.speaker === "Jesus") {
      return (
        <span key={idx} className="text-red-600 dark:text-red-500">
          {segment.content}
        </span>
      );
    } else if (segment.type === "speaker") {
      // Other speakers - could add different colors later
      return (
        <span key={idx} className="text-blue-600 dark:text-blue-400">
          {segment.content}
        </span>
      );
    }
    return <span key={idx}>{segment.content}</span>;
  });
}
