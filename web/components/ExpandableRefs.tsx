"use client";

import { useState } from "react";
import Link from "next/link";
import { getBookName } from "@/lib/books";

interface RefEntry {
  book: string;
  chapter: number;
  verses: number[];
}

function formatVerses(verses: number[]): string {
  if (verses.length === 1) return verses[0].toString();
  const isConsecutive = verses.every(
    (v, i) => i === 0 || v === verses[i - 1] + 1
  );
  if (isConsecutive && verses.length > 2) {
    return `${verses[0]}-${verses[verses.length - 1]}`;
  }
  return verses.join(", ");
}

function countRefs(refs: RefEntry[]): number {
  return refs.reduce((sum, r) => sum + r.verses.length, 0);
}

export function ExpandableRefs({
  appearsIn,
  greekAppearsIn,
  greekLabel,
  initialCount = 4,
}: {
  appearsIn: RefEntry[];
  greekAppearsIn?: RefEntry[];
  greekLabel?: string;
  initialCount?: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const [greekExpanded, setGreekExpanded] = useState(false);

  const hasMore = appearsIn.length > initialCount;
  const visible = expanded ? appearsIn : appearsIn.slice(0, initialCount);

  const hasGreek = greekAppearsIn && greekAppearsIn.length > 0;
  const greekHasMore = hasGreek && greekAppearsIn.length > initialCount;
  const greekVisible = hasGreek
    ? greekExpanded
      ? greekAppearsIn
      : greekAppearsIn.slice(0, initialCount)
    : [];

  return (
    <div className="space-y-3 pt-3 border-t border-neutral-200 dark:border-neutral-700">
      {/* Primary: English rendering matches */}
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mr-1">
          Examples ({countRefs(appearsIn)}):
        </span>
        {visible.map((ref) => (
          <Link
            key={`${ref.book}-${ref.chapter}`}
            href={`/${ref.book}/${ref.chapter}#${ref.verses[0]}`}
            className="text-sm text-amber-700 dark:text-amber-500 hover:underline"
          >
            {getBookName(ref.book)} {ref.chapter}:{formatVerses(ref.verses)}
          </Link>
        ))}
        {hasMore && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-amber-700 dark:text-amber-500 hover:underline cursor-pointer"
          >
            {expanded
              ? "Show less"
              : `+${appearsIn.length - initialCount} more`}
          </button>
        )}
      </div>

      {/* Secondary: Greek lemma matches (different English) */}
      {hasGreek && (
        <div className="flex flex-wrap gap-2">
          <span className="text-xs text-neutral-400 dark:text-neutral-500 uppercase tracking-wide mr-1">
            {greekLabel
              ? `Also from ${greekLabel} (${countRefs(greekAppearsIn)}):`
              : `Greek also in (${countRefs(greekAppearsIn)}):`}
          </span>
          {greekVisible.map((ref) => (
            <Link
              key={`greek-${ref.book}-${ref.chapter}`}
              href={`/${ref.book}/${ref.chapter}#${ref.verses[0]}`}
              className="text-sm text-neutral-500 dark:text-neutral-400 hover:underline"
            >
              {getBookName(ref.book)} {ref.chapter}:{formatVerses(ref.verses)}
            </Link>
          ))}
          {greekHasMore && (
            <button
              onClick={() => setGreekExpanded(!greekExpanded)}
              className="text-sm text-neutral-500 dark:text-neutral-400 hover:underline cursor-pointer"
            >
              {greekExpanded
                ? "Show less"
                : `+${greekAppearsIn.length - initialCount} more`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
