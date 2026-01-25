import { Metadata } from "next";
import Link from "next/link";
import {
  glossaryTerms,
  glossaryCategories,
  type GlossaryTerm,
} from "@/lib/glossary";
import { getBookName } from "@/lib/books";

export const metadata: Metadata = {
  title: "Glossary | AIT Bible",
  description:
    "Understanding key terms in the AIT Bible translation — where and why we differ from traditional renderings.",
};

export default function GlossaryPage() {
  // Group terms by category
  const termsByCategory = glossaryTerms.reduce(
    (acc, term) => {
      if (!acc[term.category]) {
        acc[term.category] = [];
      }
      acc[term.category].push(term);
      return acc;
    },
    {} as Record<string, GlossaryTerm[]>
  );

  // Sort categories by the order in glossaryCategories
  const categoryOrder = Object.keys(glossaryCategories);

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-10">
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

      {/* Category sections */}
      <div className="space-y-12">
        {categoryOrder.map((categoryId) => {
          const terms = termsByCategory[categoryId];
          if (!terms || terms.length === 0) return null;

          const category = glossaryCategories[categoryId];

          return (
            <section key={categoryId}>
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
                  {category.name}
                </h2>
                <p className="text-neutral-600 dark:text-neutral-400 mt-1">
                  {category.description}
                </p>
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
      className="scroll-mt-24 p-5 rounded-xl bg-neutral-50 dark:bg-neutral-800/50 border border-neutral-200 dark:border-neutral-700"
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

      {/* Appears In */}
      {term.appearsIn.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-3 border-t border-neutral-200 dark:border-neutral-700">
          <span className="text-xs text-neutral-500 dark:text-neutral-400 uppercase tracking-wide mr-1">
            Examples:
          </span>
          {term.appearsIn.slice(0, 4).map((ref, idx) => (
            <Link
              key={idx}
              href={`/${ref.book}/${ref.chapter}#${ref.verses[0]}`}
              className="text-sm text-amber-700 dark:text-amber-500 hover:underline"
            >
              {getBookName(ref.book)} {ref.chapter}:{formatVerses(ref.verses)}
            </Link>
          ))}
          {term.appearsIn.length > 4 && (
            <span className="text-sm text-neutral-500 dark:text-neutral-400">
              +{term.appearsIn.length - 4} more
            </span>
          )}
        </div>
      )}
    </article>
  );
}

/**
 * Format verse numbers for display
 */
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

/**
 * Simple markdown rendering for italics and bold
 */
function renderMarkdown(text: string): React.ReactNode {
  // Handle both **bold** and *italic* patterns
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);

  return parts.map((part, idx) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      // Bold - render as strong with Greek font for Greek terms
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
