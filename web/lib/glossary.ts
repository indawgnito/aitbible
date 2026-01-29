/**
 * Glossary utilities for AIT Bible
 *
 * Provides access to glossary terms and helper functions
 * for detecting and rendering glossary words in verse text.
 */

import glossaryData from "@/data/glossary.json";

export interface GlossaryTerm {
  id: string;
  greek: string;
  lemma: string;
  aitRendering: string;
  traditional: string;
  category: string;
  brief: string;
  context: string;
  appearsIn: { book: string; chapter: number; verses: number[] }[];
  greekAppearsIn: { book: string; chapter: number; verses: number[] }[];
}

export interface GlossaryCategory {
  name: string;
  description: string;
}

// Export typed glossary data
export const glossaryTerms: GlossaryTerm[] = glossaryData.terms as GlossaryTerm[];
export const glossaryCategories: Record<string, GlossaryCategory> =
  glossaryData.categories as Record<string, GlossaryCategory>;

/**
 * Get a glossary term by its ID
 */
export function getGlossaryTerm(id: string): GlossaryTerm | undefined {
  return glossaryTerms.find((term) => term.id === id);
}

/**
 * Get a glossary term by its AIT rendering (case-insensitive)
 */
export function getTermByRendering(rendering: string): GlossaryTerm | undefined {
  const lower = rendering.toLowerCase();
  return glossaryTerms.find(
    (term) => term.aitRendering.toLowerCase() === lower
  );
}

/**
 * Get all terms in a specific category
 */
export function getTermsByCategory(category: string): GlossaryTerm[] {
  return glossaryTerms.filter((term) => term.category === category);
}

/**
 * Get terms that appear in a specific book/chapter
 */
export function getTermsForChapter(
  bookId: string,
  chapter: number
): GlossaryTerm[] {
  return glossaryTerms.filter((term) =>
    term.appearsIn.some(
      (ref) => ref.book === bookId && ref.chapter === chapter
    )
  );
}

/**
 * Build a map of words to watch for in verse text.
 * Returns a map of lowercase word -> term for efficient lookup.
 */
export function buildTermLookup(): Map<string, GlossaryTerm> {
  const lookup = new Map<string, GlossaryTerm>();

  for (const term of glossaryTerms) {
    // Handle slash-separated alternative renderings (e.g. "Messiah / Anointed")
    const alternatives = term.aitRendering.includes(" / ")
      ? term.aitRendering.split(" / ").map((s) => s.trim())
      : [term.aitRendering];

    for (const alt of alternatives) {
      const words = alt.toLowerCase().split(/\s+/);

      // For single-word renderings, add directly
      if (words.length === 1) {
        lookup.set(words[0], term);
      } else {
        // For multi-word phrases, add the first word as a trigger
        // The full matching will be done in the render function
        lookup.set(words[0], term);
      }
    }
  }

  return lookup;
}

// Pre-built lookup for performance
export const termLookup = buildTermLookup();

/**
 * Check if a word (or phrase starting with word) matches a glossary term.
 * Only matches if the term's Greek lemma is present in the verse's lemmas.
 * Returns the term and the full matched text if found.
 */
export function matchGlossaryTerm(
  text: string,
  startIndex: number,
  verseLemmas?: Set<string>
): { term: GlossaryTerm; matchedText: string } | null {
  // Get the word at startIndex
  const remainingText = text.slice(startIndex);
  const wordMatch = remainingText.match(/^[\w'-]+/i);

  if (!wordMatch) return null;

  const firstWord = wordMatch[0].toLowerCase();

  // Check if this word could be a glossary term
  const potentialTerm = termLookup.get(firstWord);

  if (!potentialTerm) return null;

  // If we have verseLemmas, verify the Greek lemma is in the verse
  // This prevents false positives like "just" (merely) vs "just" (righteous)
  if (verseLemmas && verseLemmas.size > 0) {
    const termLemma = potentialTerm.lemma.toLowerCase();
    // Check if any part of the term's lemma matches any verse lemma
    // (handles compound lemmas like "ζωή, αἰώνιος")
    const termLemmaParts = termLemma.split(/[,\s\/]+/).map(l => l.trim()).filter(Boolean);
    const hasMatchingLemma = termLemmaParts.some(part =>
      Array.from(verseLemmas).some(vl => vl.includes(part) || part.includes(vl))
    );

    if (!hasMatchingLemma) {
      return null;
    }
  }

  // Check if the full rendering matches (handle slash-separated alternatives)
  const alternatives = potentialTerm.aitRendering.includes(" / ")
    ? potentialTerm.aitRendering.split(" / ").map((s) => s.trim())
    : [potentialTerm.aitRendering];

  for (const rendering of alternatives) {
    // For single-word terms
    if (!rendering.includes(" ")) {
      const singleWordMatch = remainingText.match(
        new RegExp(`^(${escapeRegex(rendering)})(?=[\\s.,;:!?'"\\)]|$)`, "i")
      );
      if (singleWordMatch) {
        return { term: potentialTerm, matchedText: singleWordMatch[1] };
      }
      continue;
    }

    // For multi-word phrases, check if the phrase matches
    const phraseMatch = remainingText.match(
      new RegExp(`^(${escapeRegex(rendering)})(?=[\\s.,;:!?'"\\)]|$)`, "i")
    );

    if (phraseMatch) {
      return { term: potentialTerm, matchedText: phraseMatch[1] };
    }
  }

  return null;
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Get all unique categories from the glossary
 */
export function getAllCategories(): string[] {
  return Object.keys(glossaryCategories);
}
