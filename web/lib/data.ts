import fs from "fs";
import path from "path";
import {
  parseAITXml,
  ParsedBook,
  ParsedChapter,
  ParsedVerse,
  GreekWord,
  VerseNote,
  TextSegment,
} from "./xml-parser";

// Re-export types from xml-parser for convenience
export type { ParsedBook, ParsedChapter, ParsedVerse, GreekWord, VerseNote, TextSegment };

// Legacy interfaces for backward compatibility
export interface Verse {
  verse: number;
  text: string;
  paragraphStart?: boolean;
}

export interface Chapter {
  chapter: number;
  verses: Verse[];
  notes: string;
}

export interface BookData {
  book: string;
  chapters: Chapter[];
}

const dataDir = path.join(process.cwd(), "data");
const kjvDir = path.join(dataDir, "kjv");

// Cache for parsed XML books
const bookCache = new Map<string, ParsedBook>();

/**
 * Check if XML file exists for a book (preferred format).
 */
function hasXmlFile(bookId: string): boolean {
  const xmlPath = path.join(dataDir, `${bookId.toLowerCase()}.xml`);
  return fs.existsSync(xmlPath);
}

/**
 * Get list of available books (checks for both XML and JSON).
 */
export function getAvailableBooks(): string[] {
  try {
    const files = fs.readdirSync(dataDir);
    const bookIds = new Set<string>();

    for (const f of files) {
      if (f.endsWith(".xml")) {
        bookIds.add(f.replace(".xml", ""));
      } else if (f.endsWith(".json")) {
        bookIds.add(f.replace(".json", ""));
      }
    }

    return Array.from(bookIds);
  } catch {
    return [];
  }
}

/**
 * Load and parse an XML book file.
 */
export function getXmlBookData(bookId: string): ParsedBook | null {
  const cacheKey = bookId.toLowerCase();

  // Check cache first
  if (bookCache.has(cacheKey)) {
    return bookCache.get(cacheKey)!;
  }

  try {
    const xmlPath = path.join(dataDir, `${cacheKey}.xml`);
    const content = fs.readFileSync(xmlPath, "utf-8");
    const parsed = parseAITXml(content);

    if (parsed) {
      bookCache.set(cacheKey, parsed);
    }

    return parsed;
  } catch {
    return null;
  }
}

/**
 * Get a chapter from an XML book with full data (Greek, notes, speakers).
 */
export function getXmlChapter(bookId: string, chapterNum: number): ParsedChapter | null {
  const book = getXmlBookData(bookId);
  if (!book) return null;

  return book.chapters.find((c) => c.chapter === chapterNum) ?? null;
}

/**
 * Get a single verse with full data.
 */
export function getXmlVerse(
  bookId: string,
  chapterNum: number,
  verseNum: number
): ParsedVerse | null {
  const chapter = getXmlChapter(bookId, chapterNum);
  if (!chapter) return null;

  return chapter.verses.find((v) => v.verse === verseNum) ?? null;
}

// ============================================================
// Legacy functions for backward compatibility with JSON format
// ============================================================

/**
 * Get book data (prefers XML, falls back to JSON).
 */
export function getBookData(bookId: string): BookData | null {
  // Try XML first
  if (hasXmlFile(bookId)) {
    const xmlBook = getXmlBookData(bookId);
    if (xmlBook) {
      return convertXmlToLegacy(xmlBook);
    }
  }

  // Fall back to JSON
  try {
    const filePath = path.join(dataDir, `${bookId.toLowerCase()}.json`);
    const content = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(content) as BookData;
  } catch {
    return null;
  }
}

/**
 * Get a chapter (prefers XML, falls back to JSON).
 */
export function getChapter(bookId: string, chapterNum: number): Chapter | null {
  const book = getBookData(bookId);
  if (!book) return null;

  return book.chapters.find((c) => c.chapter === chapterNum) ?? null;
}

/**
 * Check if a book exists (XML or JSON).
 */
export function bookExists(bookId: string): boolean {
  const xmlPath = path.join(dataDir, `${bookId.toLowerCase()}.xml`);
  const jsonPath = path.join(dataDir, `${bookId.toLowerCase()}.json`);
  return fs.existsSync(xmlPath) || fs.existsSync(jsonPath);
}

// KJV file name mapping (our book ID -> KJV filename)
const kjvFileNames: Record<string, string> = {
  matthew: "Matthew",
  mark: "Mark",
  luke: "Luke",
  john: "John",
  acts: "Acts",
  romans: "Romans",
  "1corinthians": "1Corinthians",
  "2corinthians": "2Corinthians",
  galatians: "Galatians",
  ephesians: "Ephesians",
  philippians: "Philippians",
  colossians: "Colossians",
  "1thessalonians": "1Thessalonians",
  "2thessalonians": "2Thessalonians",
  "1timothy": "1Timothy",
  "2timothy": "2Timothy",
  titus: "Titus",
  philemon: "Philemon",
  hebrews: "Hebrews",
  james: "James",
  "1peter": "1Peter",
  "2peter": "2Peter",
  "1john": "1John",
  "2john": "2John",
  "3john": "3John",
  jude: "Jude",
  revelation: "Revelation",
};

// Cache for KJV data
const kjvCache = new Map<string, Record<number, Record<number, string>>>();

/**
 * Load KJV book data and cache it.
 * Returns a map of chapter -> verse -> text
 */
function loadKjvBook(bookId: string): Record<number, Record<number, string>> | null {
  const cacheKey = bookId.toLowerCase();

  if (kjvCache.has(cacheKey)) {
    return kjvCache.get(cacheKey)!;
  }

  const fileName = kjvFileNames[cacheKey];
  if (!fileName) return null;

  try {
    const filePath = path.join(kjvDir, `${fileName}.json`);
    const content = fs.readFileSync(filePath, "utf-8");
    const data = JSON.parse(content);

    const bookData: Record<number, Record<number, string>> = {};

    for (const chapter of data.chapters) {
      const chapterNum = parseInt(chapter.chapter, 10);
      bookData[chapterNum] = {};

      for (const verse of chapter.verses) {
        const verseNum = parseInt(verse.verse, 10);
        bookData[chapterNum][verseNum] = verse.text;
      }
    }

    kjvCache.set(cacheKey, bookData);
    return bookData;
  } catch {
    return null;
  }
}

/**
 * Get KJV text for a specific verse.
 */
export function getKjvVerse(bookId: string, chapterNum: number, verseNum: number): string | null {
  const book = loadKjvBook(bookId);
  if (!book) return null;

  return book[chapterNum]?.[verseNum] ?? null;
}

/**
 * Get all KJV verses for a chapter.
 * Returns a map of verse number -> text
 */
export function getKjvChapter(bookId: string, chapterNum: number): Record<number, string> | null {
  const book = loadKjvBook(bookId);
  if (!book) return null;

  return book[chapterNum] ?? null;
}

/**
 * Convert parsed XML book to legacy BookData format.
 */
function convertXmlToLegacy(xmlBook: ParsedBook): BookData {
  return {
    book: xmlBook.name,
    chapters: xmlBook.chapters.map((chapter) => ({
      chapter: chapter.chapter,
      verses: chapter.verses.map((verse) => ({
        verse: verse.verse,
        text: verse.text,
        paragraphStart: verse.paragraphStart,
      })),
      // Combine all verse notes into a single string for legacy format
      notes: chapter.verses
        .flatMap((v) => v.notes)
        .map((n) => `**"${n.term}"**: ${n.explanation}`)
        .join("\n\n"),
    })),
  };
}
