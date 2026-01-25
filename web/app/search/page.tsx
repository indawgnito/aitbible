"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import type { SearchResult } from "@/lib/search";

export default function SearchPage() {
  return (
    <Suspense fallback={<SearchLoading />}>
      <SearchContent />
    </Suspense>
  );
}

function SearchLoading() {
  return (
    <div className="container-reading py-12">
      <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100 mb-8">
        Search
      </h1>
      <div className="animate-pulse">
        <div className="h-12 bg-neutral-200 dark:bg-neutral-800 rounded-lg mb-8" />
      </div>
    </div>
  );
}

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const initialQuery = searchParams.get("q") || "";

  const [query, setQuery] = useState(initialQuery);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [searched, setSearched] = useState(false);

  const performSearch = useCallback(async (searchQuery: string, offset = 0, append = false) => {
    if (searchQuery.trim().length < 3) {
      setResults([]);
      setTotal(0);
      setHasMore(false);
      setSearched(false);
      return;
    }

    if (append) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      const res = await fetch(
        `/api/search?q=${encodeURIComponent(searchQuery)}&offset=${offset}`
      );
      const data = await res.json();

      if (append) {
        setResults(prev => [...prev, ...(data.results || [])]);
      } else {
        setResults(data.results || []);
      }
      setTotal(data.total || 0);
      setHasMore(data.hasMore || false);
      setSearched(true);
    } catch (err) {
      console.error("Search error:", err);
      if (!append) {
        setResults([]);
        setTotal(0);
        setHasMore(false);
      }
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  // Search on initial load if query param exists
  useEffect(() => {
    if (initialQuery) {
      performSearch(initialQuery);
    }
  }, [initialQuery, performSearch]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim().length >= 3) {
      router.push(`/search?q=${encodeURIComponent(query)}`);
      performSearch(query);
    }
  };

  const handleLoadMore = () => {
    performSearch(initialQuery, results.length, true);
  };

  return (
    <div className="container-reading py-12">
      <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100 mb-8">
        Search
      </h1>

      {/* Search Form */}
      <form onSubmit={handleSubmit} className="mb-8">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search verses..."
            className="flex-1 px-4 py-3 rounded-lg border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 focus:outline-none focus:ring-2 focus:ring-amber-500 font-sans"
            autoFocus
          />
          <button
            type="submit"
            className="btn btn-primary font-sans disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading || query.trim().length < 3}
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
        <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400 font-sans">
          Searches both AIT translation and KJV text (min. 3 characters)
        </p>
      </form>

      {/* Results */}
      {loading && (
        <div className="text-center py-8 text-neutral-500 dark:text-neutral-400">
          Searching...
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="text-center py-8 text-neutral-500 dark:text-neutral-400">
          No results found for &quot;{initialQuery}&quot;
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-4">
          <p className="text-sm text-neutral-500 dark:text-neutral-400 font-sans mb-4">
            Showing {results.length} of {total} result{total !== 1 ? "s" : ""} for &quot;
            {initialQuery}&quot;
          </p>

          {results.map((result, idx) => (
            <SearchResultCard key={idx} result={result} query={initialQuery} />
          ))}

          {hasMore && (
            <div className="pt-4 text-center">
              <button
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="btn btn-secondary font-sans"
              >
                {loadingMore ? "Loading..." : "Load more results"}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function SearchResultCard({
  result,
  query,
}: {
  result: SearchResult;
  query: string;
}) {
  const reference = `${result.bookName} ${result.chapter}:${result.verse}`;
  const href = `/${result.bookId}/${result.chapter}#${result.verse}`;

  // Determine which text matched
  const matchedViaKjv =
    result.matchedIn.includes("kjv") && !result.matchedIn.includes("ait");

  // Highlight the query in the AIT text
  const highlightedText = highlightQuery(result.aitText, query);

  return (
    <Link href={href} className="block">
      <div className="card p-4 hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-amber-700 dark:text-amber-500 font-sans mb-1">
              {reference}
            </h3>
            <p
              className="text-neutral-700 dark:text-neutral-300 line-clamp-2"
              dangerouslySetInnerHTML={{ __html: highlightedText }}
            />
            {matchedViaKjv && result.kjvText && (
              <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400 italic">
                Matched via KJV: &quot;
                {getMatchedPhrase(result.kjvText, query)}
                &quot;
              </p>
            )}
          </div>
          <svg
            className="w-5 h-5 text-neutral-400 flex-shrink-0 mt-1"
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
        </div>
      </div>
    </Link>
  );
}

function highlightQuery(text: string, query: string): string {
  if (!query) return escapeHtml(text);

  const escaped = escapeHtml(text);
  const regex = new RegExp(`(${escapeRegex(query)})`, "gi");
  return escaped.replace(
    regex,
    '<mark class="bg-amber-200 dark:bg-amber-800 rounded px-0.5">$1</mark>'
  );
}

function getMatchedPhrase(text: string, query: string): string {
  const lowerText = text.toLowerCase();
  const lowerQuery = query.toLowerCase();
  const matchIndex = lowerText.indexOf(lowerQuery);

  if (matchIndex === -1) return query;

  // Get some context around the match
  const start = Math.max(0, matchIndex - 20);
  const end = Math.min(text.length, matchIndex + query.length + 20);

  let phrase = text.slice(start, end);
  if (start > 0) phrase = "..." + phrase;
  if (end < text.length) phrase = phrase + "...";

  return phrase;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
