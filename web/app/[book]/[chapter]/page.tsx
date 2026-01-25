import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook, getBookName } from "@/lib/books";
import { getXmlChapter, getXmlBookData, getKjvChapter } from "@/lib/data";
import { TranslationNotes } from "@/components/TranslationNotes";
import { ChapterContent } from "@/components/ChapterContent";

interface ChapterPageProps {
  params: Promise<{ book: string; chapter: string }>;
}

export async function generateMetadata({ params }: ChapterPageProps) {
  const { book, chapter } = await params;
  const bookName = getBookName(book);
  return {
    title: `${bookName} ${chapter} | AIT Bible`,
    description: `Read ${bookName} chapter ${chapter} in the AIT Bible translation`,
  };
}

export default async function ChapterPage({ params }: ChapterPageProps) {
  const { book, chapter: chapterStr } = await params;
  const chapterNum = parseInt(chapterStr, 10);

  const bookInfo = getBook(book);
  const chapterData = getXmlChapter(book, chapterNum);
  const bookData = getXmlBookData(book);

  if (!bookInfo || !chapterData || !bookData) {
    notFound();
  }

  // Determine prev/next chapters
  const prevChapter = chapterNum > 1 ? chapterNum - 1 : null;
  const nextChapter = chapterNum < bookInfo.chapters ? chapterNum + 1 : null;

  // Check if prev/next chapters exist in data
  const prevExists = prevChapter
    ? bookData.chapters.some((c) => c.chapter === prevChapter)
    : false;
  const nextExists = nextChapter
    ? bookData.chapters.some((c) => c.chapter === nextChapter)
    : false;

  // Get KJV text for comparison
  const kjvVerses = getKjvChapter(book, chapterNum) ?? {};

  // Collect all notes from this chapter for the legacy TranslationNotes component
  const allNotes = chapterData.verses
    .flatMap((v) => v.notes)
    .map((n) => `**"${n.term}"**: ${n.explanation}`)
    .join("\n\n");

  return (
    <article className="container-reading py-12">
      {/* Breadcrumb */}
      <nav className="mb-8 flex items-center gap-2 text-sm font-sans">
        <Link
          href="/"
          className="text-neutral-500 dark:text-neutral-400 hover:text-amber-700 dark:hover:text-amber-500 transition-colors"
        >
          Home
        </Link>
        <span className="text-neutral-400 dark:text-neutral-500">/</span>
        <Link
          href={`/${book}`}
          className="text-neutral-500 dark:text-neutral-400 hover:text-amber-700 dark:hover:text-amber-500 transition-colors"
        >
          {bookInfo.name}
        </Link>
        <span className="text-neutral-400 dark:text-neutral-500">/</span>
        <span className="text-neutral-700 dark:text-neutral-300">
          Chapter {chapterNum}
        </span>
      </nav>

      {/* Chapter Title */}
      <header className="mb-10">
        <h1 className="text-3xl md:text-4xl font-bold text-neutral-900 dark:text-neutral-100">
          {bookInfo.name} {chapterNum}
        </h1>
      </header>

      {/* The Translation - now with clickable verses */}
      <ChapterContent
        chapter={chapterData}
        bookName={bookInfo.name}
        chapterNum={chapterNum}
        kjvVerses={kjvVerses}
      />

      {/* Translation Notes (Collapsible) */}
      <TranslationNotes notes={allNotes} />

      {/* Chapter Navigation */}
      <nav className="mt-16 pt-8 border-t border-neutral-200 dark:border-neutral-800 flex justify-between items-center">
        {prevExists ? (
          <Link
            href={`/${book}/${prevChapter}`}
            className="btn btn-secondary font-sans text-sm"
          >
            ← Chapter {prevChapter}
          </Link>
        ) : (
          <div />
        )}

        <Link
          href={`/${book}`}
          className="text-sm text-neutral-500 dark:text-neutral-400 hover:text-amber-700 dark:hover:text-amber-500 transition-colors font-sans"
        >
          All Chapters
        </Link>

        {nextExists ? (
          <Link
            href={`/${book}/${nextChapter}`}
            className="btn btn-secondary font-sans text-sm"
          >
            Chapter {nextChapter} →
          </Link>
        ) : (
          <div />
        )}
      </nav>
    </article>
  );
}
