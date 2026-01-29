"use client";

import { useState, useCallback, useMemo } from "react";
import Link from "next/link";
import type { GlossaryTerm } from "@/lib/glossary";
import { ExpandableRefs } from "@/components/ExpandableRefs";
import { GlossaryFilter } from "@/components/GlossaryFilter";

interface CategoryMeta {
  id: string;
  name: string;
  description: string;
  count: number;
}

export function GlossaryContent({
  categories,
  termsByCategory,
}: {
  categories: CategoryMeta[];
  termsByCategory: Record<string, GlossaryTerm[]>;
}) {
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  // Filter terms by search query
  const filteredByCategory = useMemo(() => {
    if (!searchQuery.trim()) return termsByCategory;

    const q = searchQuery.toLowerCase();
    const result: Record<string, GlossaryTerm[]> = {};

    for (const [catId, terms] of Object.entries(termsByCategory)) {
      const filtered = terms.filter(
        (t) =>
          t.aitRendering.toLowerCase().includes(q) ||
          t.traditional.toLowerCase().includes(q) ||
          t.greek.toLowerCase().includes(q)
      );
      if (filtered.length > 0) {
        result[catId] = filtered;
      }
    }
    return result;
  }, [searchQuery, termsByCategory]);

  const totalFiltered = Object.values(filteredByCategory).reduce(
    (sum, terms) => sum + terms.length,
    0
  );

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
          Translation Glossary
        </h1>
        <p className="text-lg text-neutral-600 dark:text-neutral-400 leading-relaxed">
          The AIT Bible sometimes uses different words than traditional English
          translations. This glossary explains why — not to be different for its
          own sake, but to recover meaning that conventional renderings may
          obscure.
        </p>
      </div>

      {/* Sticky filter bar */}
      <GlossaryFilter categories={categories} onSearch={handleSearch} />

      {/* Results count when filtering */}
      {searchQuery.trim() && (
        <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-4">
          {totalFiltered} {totalFiltered === 1 ? "term" : "terms"} matching
          &ldquo;{searchQuery}&rdquo;
        </p>
      )}

      {/* Category sections */}
      <div className="space-y-12 mt-8">
        {categories.map((cat) => {
          const terms = filteredByCategory[cat.id];
          if (!terms || terms.length === 0) return null;

          return (
            <section key={cat.id} id={`category-${cat.id}`} className="scroll-mt-32">
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
                  {cat.name}
                  <span className="ml-2 text-base font-normal text-neutral-400 dark:text-neutral-500">
                    ({terms.length})
                  </span>
                </h2>
                {!searchQuery.trim() && (
                  <p className="text-neutral-600 dark:text-neutral-400 mt-1">
                    {cat.description}
                  </p>
                )}
              </div>

              <div className="space-y-6">
                {terms.map((term) => (
                  <GlossaryEntry key={term.id} term={term} />
                ))}
              </div>
            </section>
          );
        })}
      </div>

      {totalFiltered === 0 && searchQuery.trim() && (
        <p className="text-neutral-500 dark:text-neutral-400 text-center py-12">
          No glossary terms match your search.
        </p>
      )}

      {/* Back link */}
      <div className="mt-12 pt-8 border-t border-neutral-200 dark:border-neutral-800">
        <Link
          href="/"
          className="text-amber-700 dark:text-amber-500 hover:underline"
        >
          &larr; Back to reading
        </Link>
      </div>
    </main>
  );
}

function GlossaryEntry({ term }: { term: GlossaryTerm }) {
  return (
    <article
      id={term.id}
      className="scroll-mt-32 p-5 rounded-xl bg-neutral-50 dark:bg-neutral-800/50 border border-neutral-200 dark:border-neutral-700"
    >
      {/* Header */}
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 mb-3">
        <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
          {term.aitRendering}
        </h3>
        <span className="text-lg text-neutral-500 dark:text-neutral-400 font-greek">
          {term.greek}
        </span>
        <span className="text-sm text-neutral-500 dark:text-neutral-400">
          (traditional: &quot;{term.traditional}&quot;)
        </span>
      </div>

      {/* Brief */}
      <p className="text-neutral-700 dark:text-neutral-300 mb-4">
        {renderMarkdown(term.brief)}
      </p>

      {/* Context */}
      <div className="text-sm text-neutral-600 dark:text-neutral-400 leading-relaxed space-y-2 mb-4">
        {term.context.split("\n\n").map((paragraph, idx) => (
          <p key={idx}>{renderMarkdown(paragraph)}</p>
        ))}
      </div>

      {/* Appears In (dual refs) */}
      {(term.appearsIn.length > 0 || term.greekAppearsIn?.length > 0) && (
        <ExpandableRefs
          appearsIn={term.appearsIn}
          greekAppearsIn={term.greekAppearsIn}
          greekLabel={term.greek}
          initialCount={4}
        />
      )}
    </article>
  );
}

function renderMarkdown(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);

  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={idx} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("*") && part.endsWith("*")) {
      return (
        <em key={idx} className="font-greek">
          {part.slice(1, -1)}
        </em>
      );
    }
    return part;
  });
}
