"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import type { GlossaryTerm } from "@/lib/glossary";
import { glossaryCategories } from "@/lib/glossary";
import { getBookName } from "@/lib/books";

interface WordModalProps {
  isOpen: boolean;
  onClose: () => void;
  term: GlossaryTerm | null;
}

export function WordModal({ isOpen, onClose, term }: WordModalProps) {
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

  if (!isOpen || !term) return null;

  const category = glossaryCategories[term.category];

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
        <div className="sticky top-0 bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-800 px-6 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
                {term.aitRendering}
              </h2>
              <p className="text-lg text-neutral-600 dark:text-neutral-400 font-greek mt-0.5">
                {term.greek}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 -m-2 text-neutral-500 hover:text-neutral-900 dark:hover:text-neutral-100 transition-colors cursor-pointer flex-shrink-0"
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
        </div>

        {/* Content */}
        <div className="px-6 py-5 space-y-5">
          {/* Category & Traditional */}
          <div className="flex flex-wrap gap-2">
            {category && (
              <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400">
                {category.name}
              </span>
            )}
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-neutral-100 text-neutral-600 dark:bg-neutral-800 dark:text-neutral-400">
              Traditional: &quot;{term.traditional}&quot;
            </span>
          </div>

          {/* Brief */}
          <p className="text-lg text-neutral-700 dark:text-neutral-300 leading-relaxed">
            {renderMarkdown(term.brief)}
          </p>

          {/* Full Context */}
          <section>
            <h3 className="text-xs font-sans font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-3">
              Why This Translation?
            </h3>
            <div className="text-neutral-700 dark:text-neutral-300 leading-relaxed space-y-3">
              {term.context.split("\n\n").map((paragraph, idx) => (
                <p key={idx}>{renderMarkdown(paragraph)}</p>
              ))}
            </div>
          </section>

          {/* Appears In */}
          {term.appearsIn.length > 0 && (
            <AppearsInSection
              appearsIn={term.appearsIn}
              greekAppearsIn={term.greekAppearsIn}
              greekLabel={term.greek}
              onClose={onClose}
            />
          )}
          {term.appearsIn.length === 0 &&
            term.greekAppearsIn &&
            term.greekAppearsIn.length > 0 && (
              <GreekOnlySection
                greekAppearsIn={term.greekAppearsIn}
                greekLabel={term.greek}
                onClose={onClose}
              />
            )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-neutral-900 border-t border-neutral-200 dark:border-neutral-800 px-6 py-4">
          <Link
            href={`/glossary#${term.id}`}
            onClick={onClose}
            className="btn btn-secondary w-full flex items-center justify-center gap-2 font-sans text-sm"
          >
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
                d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
              />
            </svg>
            View in Glossary
          </Link>
        </div>
      </div>
    </div>
  );
}

/**
 * Expandable "Appears In" section with show more/less toggle.
 */
function countRefs(refs: { verses: number[] }[]): number {
  return refs.reduce((sum, r) => sum + r.verses.length, 0);
}

function AppearsInSection({
  appearsIn,
  greekAppearsIn,
  greekLabel,
  onClose,
}: {
  appearsIn: GlossaryTerm["appearsIn"];
  greekAppearsIn?: GlossaryTerm["greekAppearsIn"];
  greekLabel?: string;
  onClose: () => void;
}) {
  const INITIAL_COUNT = 6;
  const [expanded, setExpanded] = useState(false);
  const [greekExpanded, setGreekExpanded] = useState(false);

  const hasMore = appearsIn.length > INITIAL_COUNT;
  const visible = expanded ? appearsIn : appearsIn.slice(0, INITIAL_COUNT);

  const hasGreek = greekAppearsIn && greekAppearsIn.length > 0;
  const greekHasMore = hasGreek && greekAppearsIn.length > INITIAL_COUNT;
  const greekVisible = hasGreek
    ? greekExpanded
      ? greekAppearsIn
      : greekAppearsIn.slice(0, INITIAL_COUNT)
    : [];

  return (
    <section className="space-y-4">
      <div>
        <h3 className="text-xs font-sans font-semibold uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-3">
          Used in translation ({countRefs(appearsIn)})
        </h3>
        <div className="flex flex-wrap gap-2">
          {visible.map((ref) => (
            <Link
              key={`${ref.book}-${ref.chapter}`}
              href={`/${ref.book}/${ref.chapter}#${ref.verses[0]}`}
              onClick={onClose}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm bg-neutral-100 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700 text-neutral-700 dark:text-neutral-300 transition-colors"
            >
              {getBookName(ref.book)} {ref.chapter}:{formatVerses(ref.verses)}
            </Link>
          ))}
          {hasMore && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm text-amber-700 dark:text-amber-500 hover:bg-amber-50 dark:hover:bg-amber-900/20 transition-colors cursor-pointer"
            >
              {expanded
                ? "Show less"
                : `+${appearsIn.length - INITIAL_COUNT} more`}
            </button>
          )}
        </div>
      </div>

      {hasGreek && (
        <div>
          <h3 className="text-xs font-sans font-semibold uppercase tracking-wide text-neutral-400 dark:text-neutral-500 mb-3">
            {greekLabel
              ? `${greekLabel} also in (${countRefs(greekAppearsIn)})`
              : `Greek also in (${countRefs(greekAppearsIn)})`}
          </h3>
          <div className="flex flex-wrap gap-2">
            {greekVisible.map((ref) => (
              <Link
                key={`greek-${ref.book}-${ref.chapter}`}
                href={`/${ref.book}/${ref.chapter}#${ref.verses[0]}`}
                onClick={onClose}
                className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm bg-neutral-50 hover:bg-neutral-100 dark:bg-neutral-800/50 dark:hover:bg-neutral-800 text-neutral-500 dark:text-neutral-400 transition-colors"
              >
                {getBookName(ref.book)} {ref.chapter}:
                {formatVerses(ref.verses)}
              </Link>
            ))}
            {greekHasMore && (
              <button
                onClick={() => setGreekExpanded(!greekExpanded)}
                className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
              >
                {greekExpanded
                  ? "Show less"
                  : `+${greekAppearsIn.length - INITIAL_COUNT} more`}
              </button>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function GreekOnlySection({
  greekAppearsIn,
  greekLabel,
  onClose,
}: {
  greekAppearsIn: GlossaryTerm["greekAppearsIn"];
  greekLabel?: string;
  onClose: () => void;
}) {
  const INITIAL_COUNT = 6;
  const [expanded, setExpanded] = useState(false);
  const hasMore = greekAppearsIn.length > INITIAL_COUNT;
  const visible = expanded
    ? greekAppearsIn
    : greekAppearsIn.slice(0, INITIAL_COUNT);

  return (
    <section>
      <h3 className="text-xs font-sans font-semibold uppercase tracking-wide text-neutral-400 dark:text-neutral-500 mb-3">
        {greekLabel
          ? `${greekLabel} appears in (${countRefs(greekAppearsIn)})`
          : `Greek appears in (${countRefs(greekAppearsIn)})`}
      </h3>
      <div className="flex flex-wrap gap-2">
        {visible.map((ref) => (
          <Link
            key={`greek-${ref.book}-${ref.chapter}`}
            href={`/${ref.book}/${ref.chapter}#${ref.verses[0]}`}
            onClick={onClose}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm bg-neutral-50 hover:bg-neutral-100 dark:bg-neutral-800/50 dark:hover:bg-neutral-800 text-neutral-500 dark:text-neutral-400 transition-colors"
          >
            {getBookName(ref.book)} {ref.chapter}:{formatVerses(ref.verses)}
          </Link>
        ))}
        {hasMore && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm text-neutral-500 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors cursor-pointer"
          >
            {expanded
              ? "Show less"
              : `+${greekAppearsIn.length - INITIAL_COUNT} more`}
          </button>
        )}
      </div>
    </section>
  );
}

/**
 * Format verse numbers for display (e.g., [1, 2, 3] -> "1-3")
 */
function formatVerses(verses: number[]): string {
  if (verses.length === 1) return verses[0].toString();

  // Check if consecutive
  const isConsecutive = verses.every(
    (v, i) => i === 0 || v === verses[i - 1] + 1
  );

  if (isConsecutive && verses.length > 2) {
    return `${verses[0]}-${verses[verses.length - 1]}`;
  }

  return verses.join(", ");
}

/**
 * Simple markdown rendering for italics and bold
 */
function renderMarkdown(text: string): React.ReactNode {
  // Handle both **bold** and *italic* patterns
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);

  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      // Bold
      return (
        <strong key={idx} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      // Italic - typically for Greek terms
      return (
        <em key={idx} className="font-greek">
          {part.slice(1, -1)}
        </em>
      );
    }
    return part;
  });
}
