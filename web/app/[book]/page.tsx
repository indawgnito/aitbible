import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook, getBookName } from "@/lib/books";
import { getBookData } from "@/lib/data";

interface BookPageProps {
  params: Promise<{ book: string }>;
}

export async function generateMetadata({ params }: BookPageProps) {
  const { book } = await params;
  const bookName = getBookName(book);
  return {
    title: `${bookName} | AIT Bible`,
    description: `Read the AIT Bible translation of ${bookName}`,
  };
}

export default async function BookPage({ params }: BookPageProps) {
  const { book } = await params;
  const bookInfo = getBook(book);
  const bookData = getBookData(book);

  if (!bookInfo || !bookData) {
    notFound();
  }

  return (
    <div className="container-reading py-12">
      {/* Breadcrumb */}
      <nav className="mb-8">
        <Link
          href="/"
          className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-amber-700 dark:hover:text-amber-500 transition-colors font-sans"
        >
          ← All Books
        </Link>
      </nav>

      {/* Book Title */}
      <h1 className="text-3xl md:text-4xl font-bold text-neutral-900 dark:text-neutral-100 mb-8">
        {bookInfo.name}
      </h1>

      {/* Chapter Grid */}
      <div className="grid grid-cols-4 md:grid-cols-7 gap-2">
        {Array.from({ length: bookInfo.chapters }, (_, i) => i + 1).map(
          (chapter) => {
            const hasChapter = bookData.chapters.some(
              (c) => c.chapter === chapter
            );

            if (hasChapter) {
              return (
                <Link
                  key={chapter}
                  href={`/${book}/${chapter}`}
                  className="card p-4 text-center hover:border-amber-500 dark:hover:border-amber-600 transition-colors group"
                >
                  <span className="font-sans font-medium text-neutral-900 dark:text-neutral-100 group-hover:text-amber-700 dark:group-hover:text-amber-500 transition-colors">
                    {chapter}
                  </span>
                </Link>
              );
            }

            return (
              <div
                key={chapter}
                className="card p-4 text-center opacity-50 cursor-not-allowed"
              >
                <span className="font-sans font-medium text-neutral-400 dark:text-neutral-500">
                  {chapter}
                </span>
              </div>
            );
          }
        )}
      </div>
    </div>
  );
}
