import Link from "next/link";
import { books } from "@/lib/books";
import { getAvailableBooks } from "@/lib/data";
import { TranslationCarousel } from "@/components/TranslationCarousel";

export default function Home() {
  const availableBooks = getAvailableBooks();

  return (
    <div className="container-reading py-16">
      {/* Hero */}
      <div className="text-center mb-16">
        <h1 className="text-4xl md:text-5xl font-bold text-neutral-900 dark:text-neutral-100 mb-6">
          AIT Bible
        </h1>
        <p className="text-xl text-neutral-600 dark:text-neutral-400 max-w-xl mx-auto leading-relaxed">
          An AI translation of the Greek New Testament that shows its work.
        </p>
      </div>

      {/* Translation Example */}
      <TranslationCarousel />

      {/* About */}
      <div className="card p-8 mb-12">
        <h2 className="font-sans font-semibold text-lg text-neutral-900 dark:text-neutral-100 mb-4">
          What This Is
        </h2>
        <div className="space-y-4 text-neutral-700 dark:text-neutral-300">
          <p>
            The AIT Bible is a translation of the Greek New Testament made by
            an AI model, with one aim: to say in plain modern English what a
            first-century reader would have understood.
          </p>
          <p>
            Where the traditional English word now misleads, the text departs
            from it. Where the traditional word is still the best one, the
            text keeps it. Departures come with a note that gives the
            traditional wording, the reason for the change, and what most
            scholars think, so you can disagree with it.
          </p>
          <p>
            The decisions that shape the translation are public: the prompt,
            the list of word choices, and the raw output of every chapter are
            in the repository. Each word on that list is rendered the same
            way from Matthew to Revelation, and an audit checks it.
          </p>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            This is a machine translation that has not been reviewed by
            scholars. Treat it as a study aid beside an established
            translation, not as a replacement for one.{" "}
            <Link
              href="/vision"
              className="text-amber-700 dark:text-amber-500 hover:underline font-medium font-sans"
            >
              How it was made →
            </Link>
          </p>
        </div>
      </div>

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
                    {book.chapters} chapters
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
