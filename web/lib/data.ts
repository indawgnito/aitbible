import fs from "fs";
import path from "path";

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

export function getAvailableBooks(): string[] {
  try {
    const files = fs.readdirSync(dataDir);
    return files
      .filter((f) => f.endsWith(".json"))
      .map((f) => f.replace(".json", ""));
  } catch {
    return [];
  }
}

export function getBookData(bookId: string): BookData | null {
  try {
    const filePath = path.join(dataDir, `${bookId.toLowerCase()}.json`);
    const content = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(content) as BookData;
  } catch {
    return null;
  }
}

export function getChapter(bookId: string, chapterNum: number): Chapter | null {
  const book = getBookData(bookId);
  if (!book) return null;

  return book.chapters.find((c) => c.chapter === chapterNum) ?? null;
}

export function bookExists(bookId: string): boolean {
  const filePath = path.join(dataDir, `${bookId.toLowerCase()}.json`);
  return fs.existsSync(filePath);
}
