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
          A fresh translation from the original Greek, prioritizing accuracy and
          meaning over tradition.
        </p>
      </div>

      {/* Translation Example */}
      <TranslationCarousel />

      {/* About */}
      <div className="card p-8 mb-12">
        <h2 className="font-sans font-semibold text-lg text-neutral-900 dark:text-neutral-100 mb-4">
          Why This Translation?
        </h2>
        <div className="space-y-4 text-neutral-700 dark:text-neutral-300">
          <p>
            In 1997, world chess champion Garry Kasparov lost to Deep Blue,
            IBM&rsquo;s chess-playing computer. Today, no one questions using
            chess engines for analysis—the tool simply sees more than we can. We
            believe language translation is now crossing a similar threshold.
          </p>
          <p>
            Modern AI can hold the entirety of ancient Greek, centuries of
            linguistic context, and semantic patterns across thousands of texts
            in view simultaneously. No individual translator—however skilled—can
            match that scope. This isn&rsquo;t about replacing human judgment,
            but simply recognizing when a tool can see better than we can alone.
          </p>
          <p>
            Traditional translations also carry accumulated meaning. Words like
            &ldquo;hypocrites&rdquo; have gathered connotations over centuries
            that obscure what the original Greek audience would have understood.
            AI helps us cut through those layers and ask:{" "}
            <em>
              What did this actually mean to the people who first heard it?
            </em>
          </p>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            This is an ongoing project. AI is imperfect, and we approach this
            work with humility and transparency.{" "}
            <Link
              href="/vision"
              className="text-amber-700 dark:text-amber-500 hover:underline font-medium font-sans"
            >
              Read our full vision →
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

      {/* Old Testament */}
      <div className="mt-12">
        <h2 className="font-sans font-semibold text-sm uppercase tracking-wide text-neutral-500 dark:text-neutral-400 mb-6">
          Old Testament
        </h2>
        <div className="card p-8 text-center">
          <span className="text-neutral-500 dark:text-neutral-400">
            Coming soon
          </span>
        </div>
      </div>
    </div>
  );
}
