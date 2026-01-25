/**
 * Search functionality for AIT Bible
 *
 * Searches across both AIT translation and KJV text,
 * returning AIT verse results.
 */

import { getXmlBookData, getKjvChapter } from "./data";
import { books } from "./books";

export interface SearchResult {
  bookId: string;
  bookName: string;
  chapter: number;
  verse: number;
  aitText: string;
  kjvText: string | null;
  matchedIn: ("ait" | "kjv")[];
}

export interface SearchOptions {
  limit?: number;
  offset?: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  hasMore: boolean;
}

/**
 * Search all books for verses matching the query.
 * Matches against both AIT and KJV text (case-insensitive).
 * Returns paginated results with total count.
 */
export function searchVerses(
  query: string,
  options: SearchOptions = {}
): SearchResponse {
  const { limit = 10, offset = 0 } = options;

  if (!query || query.trim().length < 3) {
    return { results: [], total: 0, hasMore: false };
  }

  const searchTerm = query.toLowerCase().trim();
  const allMatches: SearchResult[] = [];

  // Cap total matches we'll collect to prevent memory issues
  const maxTotal = 500;

  for (const bookInfo of books) {
    if (allMatches.length >= maxTotal) break;

    const book = getXmlBookData(bookInfo.id);
    if (!book) continue;

    const bookName = bookInfo.name;

    for (const chapter of book.chapters) {
      if (allMatches.length >= maxTotal) break;

      // Get KJV chapter for comparison
      const kjvChapter = getKjvChapter(bookInfo.id, chapter.chapter);

      for (const verse of chapter.verses) {
        if (allMatches.length >= maxTotal) break;

        const aitText = verse.text;
        const kjvText = kjvChapter?.[verse.verse] ?? null;

        const matchedIn: ("ait" | "kjv")[] = [];

        // Check AIT text
        if (aitText.toLowerCase().includes(searchTerm)) {
          matchedIn.push("ait");
        }

        // Check KJV text
        if (kjvText && kjvText.toLowerCase().includes(searchTerm)) {
          matchedIn.push("kjv");
        }

        // If matched in either, add to results
        if (matchedIn.length > 0) {
          allMatches.push({
            bookId: bookInfo.id,
            bookName,
            chapter: chapter.chapter,
            verse: verse.verse,
            aitText,
            kjvText,
            matchedIn,
          });
        }
      }
    }
  }

  const total = allMatches.length;
  const results = allMatches.slice(offset, offset + limit);
  const hasMore = offset + limit < total;

  return { results, total, hasMore };
}

/**
 * Create a highlighted snippet from text around the matched term.
 */
export function createSnippet(
  text: string,
  query: string,
  contextChars: number = 40
): string {
  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const matchIndex = lowerText.indexOf(lowerQuery);

  if (matchIndex === -1) {
    // No match, return truncated text
    return text.length > contextChars * 2
      ? text.slice(0, contextChars * 2) + "..."
      : text;
  }

  const start = Math.max(0, matchIndex - contextChars);
  const end = Math.min(text.length, matchIndex + query.length + contextChars);

  let snippet = text.slice(start, end);

  // Add ellipsis if truncated
  if (start > 0) snippet = "..." + snippet;
  if (end < text.length) snippet = snippet + "...";

  return snippet;
}

/**
 * Highlight matched terms in text by wrapping them in <mark> tags.
 * Returns HTML string.
 */
export function highlightMatches(text: string, query: string): string {
  if (!query) return text;

  const regex = new RegExp(`(${escapeRegex(query)})`, "gi");
  return text.replace(regex, "<mark>$1</mark>");
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
