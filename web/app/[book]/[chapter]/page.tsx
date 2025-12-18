import Link from "next/link";
import { notFound } from "next/navigation";
import { getBook, getBookName } from "@/lib/books";
import { getChapter, getBookData } from "@/lib/data";
import { TranslationNotes } from "@/components/TranslationNotes";

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
  const chapterData = getChapter(book, chapterNum);
  const bookData = getBookData(book);

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

      {/* The Translation */}
      <div className="prose-reading">
        {(() => {
          // Group verses into paragraphs
          const paragraphs: (typeof chapterData.verses)[] = [];
          let currentParagraph: typeof chapterData.verses = [];

          chapterData.verses.forEach((verse, index) => {
            if (verse.paragraphStart && currentParagraph.length > 0) {
              paragraphs.push(currentParagraph);
              currentParagraph = [];
            }
            currentParagraph.push(verse);
          });
          if (currentParagraph.length > 0) {
            paragraphs.push(currentParagraph);
          }

          return paragraphs.map((paragraph, pIndex) => (
            <p key={pIndex} className="mb-4">
              {paragraph.map((verse) => {
                // Split the text to grab the first word
                const words = verse.text.trim().split(" ");
                const firstWord = words[0];
                const restOfText = words.slice(1).join(" ");

                return (
                  <span key={verse.verse}>
                    {/* The wrapper ensures the number and first word stay together */}
                    <span className="verse-wrapper">
                      <sup className="verse-num">{verse.verse}</sup>
                      {firstWord}
                    </span>
                    {/* Add a space and the rest of the text */} {restOfText}{" "}
                  </span>
                );
              })}
            </p>
          ));
        })()}
      </div>

      {/* Translation Notes (Collapsible) */}
      <TranslationNotes notes={chapterData.notes} />

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
