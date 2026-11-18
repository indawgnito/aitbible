import Link from "next/link";
import { books } from "@/lib/books";
import { getAvailableBooks } from "@/lib/data";
import { TranslationCarousel } from "@/components/TranslationCarousel";

export default function Home() {
  const availableBooks = getAvailableBooks();

  return (
    <div className="container-reading py-16">
      {/* Hero */}
      <div className="text-center mb-10">
        <h1 className="text-4xl md:text-5xl font-bold text-neutral-900 dark:text-neutral-100 mb-6">
          AIT Bible
        </h1>
        <p className="text-xl text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto leading-relaxed">
          An AI translation of the Greek New Testament that shows its work.
        </p>
      </div>

      {/* About */}
      <div className="mb-12 space-y-4 text-neutral-700 dark:text-neutral-300">
        <p>
          The AIT Bible is a translation of the Greek New Testament made by
          an AI model. It aims to say in plain modern English what a
          first-century reader would have understood, and it explains itself:
          where the text departs from the traditional wording, a note gives
          the reason and what most scholars think.
        </p>
        <p className="text-sm text-neutral-600 dark:text-neutral-400">
          This is a machine translation that has not been reviewed by
          scholars. Read it beside an established translation, not in place
          of one.
        </p>
        <div className="flex flex-wrap items-center gap-4 pt-2 font-sans">
          <Link
            href="/matthew/1"
            className="px-5 py-2.5 rounded-lg bg-amber-700 hover:bg-amber-800 text-white font-medium transition-colors"
          >
            Start reading
          </Link>
          <Link
            href="/vision"
            className="text-amber-700 dark:text-amber-500 hover:underline font-medium"
          >
            How it was made →
          </Link>
        </div>
      </div>

      {/* Translation Example */}
      <TranslationCarousel />

      {/* Book List */}
      <div>
        <h2 className="font-sans font-semibold text-sm uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-6">
          New Testament
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {books.map((book) => {
            const isAvailable = availableBooks.includes(book.id);

            if (isAvailable) {
              return (
                <Link
                  key={book.id}
                  href={`/${book.id}`}
                  className="card p-4 hover:border-amber-500 dark:hover:border-amber-600 transition-colors group"
                >
                  <span className="font-sans font-medium text-neutral-900 dark:text-neutral-100 group-hover:text-amber-700 dark:group-hover:text-amber-500 transition-colors">
                    {book.name}
                  </span>
                  <span className="block text-sm text-neutral-500 dark:text-neutral-400 mt-1">
                    {book.chapters} {book.chapters === 1 ? "chapter" : "chapters"}
                  </span>
                </Link>
              );
            }

            return (
              <div
                key={book.id}
                className="card p-4 opacity-50 cursor-not-allowed"
              >
                <span className="font-sans font-medium text-neutral-500 dark:text-neutral-400">
                  {book.name}
                </span>
                <span className="block text-sm text-neutral-400 dark:text-neutral-500 mt-1">
                  Coming soon
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
