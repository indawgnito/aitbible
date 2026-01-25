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
    // Add the main AIT rendering
    const words = term.aitRendering.toLowerCase().split(/\s+/);

    // For single-word renderings, add directly
    if (words.length === 1) {
      lookup.set(words[0], term);
    } else {
      // For multi-word phrases, add the first word as a trigger
      // The full matching will be done in the render function
      lookup.set(words[0], term);
    }
  }

  return lookup;
}

// Pre-built lookup for performance
export const termLookup = buildTermLookup();

/**
 * Check if a word (or phrase starting with word) matches a glossary term.
 * Returns the term and the full matched text if found.
 */
export function matchGlossaryTerm(
  text: string,
  startIndex: number
): { term: GlossaryTerm; matchedText: string } | null {
  // Get the word at startIndex
  const remainingText = text.slice(startIndex);
  const wordMatch = remainingText.match(/^[\w'-]+/i);

  if (!wordMatch) return null;

  const firstWord = wordMatch[0].toLowerCase();

  // Check if this word could be a glossary term
  const potentialTerm = termLookup.get(firstWord);

  if (!potentialTerm) return null;

  // Check if the full rendering matches
  const rendering = potentialTerm.aitRendering;
  const renderingLower = rendering.toLowerCase();

  // For single-word terms
  if (!rendering.includes(" ")) {
    // Match the word with possible punctuation after
    const singleWordMatch = remainingText.match(
      new RegExp(`^(${escapeRegex(rendering)})(?=[\\s.,;:!?'"\\)]|$)`, "i")
    );
    if (singleWordMatch) {
      return { term: potentialTerm, matchedText: singleWordMatch[1] };
    }
    return null;
  }

  // For multi-word phrases, check if the phrase matches
  const phraseMatch = remainingText.match(
    new RegExp(`^(${escapeRegex(rendering)})(?=[\\s.,;:!?'"\\)]|$)`, "i")
  );

  if (phraseMatch) {
    return { term: potentialTerm, matchedText: phraseMatch[1] };
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
