"use client";

import Link from "next/link";
import { useTheme } from "next-themes";
import { SearchBar } from "./SearchBar";

function DarkModeToggle() {
  const { resolvedTheme, setTheme } = useTheme();

  return (
    <button
      // We can use resolvedTheme safely in onClick because it runs after hydration
      onClick={() => setTheme(resolvedTheme === "dark" ? "light" : "dark")}
      className="p-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-colors group"
      aria-label="Toggle dark mode"
    >
      {/* CSS-BASED TOGGLE:
         We render BOTH icons, but use Tailwind classes to show/hide them.
         This removes the need for useEffect and eliminates the hydration error.
      */}

      {/* Sun Icon: Visible in Light Mode (block), Hidden in Dark Mode (dark:hidden) */}
      <svg
        className="w-5 h-5 text-neutral-600 block dark:hidden"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
        />
      </svg>

      {/* Moon Icon: Hidden in Light Mode (hidden), Visible in Dark Mode (dark:block) */}
      <svg
        className="w-5 h-5 text-neutral-300 hidden dark:block"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
        />
      </svg>
    </button>
  );
}

export function Header() {
  return (
    <header className="sticky top-0 z-50 backdrop-blur-sm border-b border-neutral-200 dark:border-neutral-800 bg-parchment-50/80 dark:bg-neutral-950/80">
      <div className="container-reading py-4 flex items-center justify-between">
        <Link
          href="/"
          className="font-sans font-semibold text-xl text-neutral-900 dark:text-neutral-100 hover:text-amber-700 dark:hover:text-amber-500 transition-colors"
        >
          AIT Bible
        </Link>
        <div className="flex items-center gap-3">
          <SearchBar />
          <Link
            href="/glossary"
            className="p-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-colors"
            aria-label="Glossary"
            title="Translation Glossary"
          >
            <svg
              className="w-5 h-5 text-neutral-600 dark:text-neutral-300"
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
          </Link>
          <a
            href="https://github.com/indawgnito/aitbible"
            target="_blank"
            rel="noopener noreferrer"
            className="p-2 rounded-lg hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-colors"
            aria-label="View on GitHub"
          >
            <svg
              className="w-5 h-5 text-neutral-600 dark:text-neutral-300"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                fillRule="evenodd"
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                clipRule="evenodd"
              />
            </svg>
          </a>
          <DarkModeToggle />
        </div>
      </div>
    </header>
  );
}
