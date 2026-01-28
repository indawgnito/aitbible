/**
 * XML Parser for AIT Bible format
 *
 * Parses AIT XML files into structured TypeScript objects.
 * Designed for server-side use in Next.js.
 */

import { DOMParser } from "@xmldom/xmldom";

// Types for parsed XML data

export interface GreekWord {
  text: string;
  lemma: string;
}

export interface VerseNote {
  term: string;
  explanation: string;
}

export interface TextSegment {
  type: "text" | "speaker";
  content: string;
  speaker?: string; // e.g., "Jesus", "God", "angel"
}

export interface ParsedVerse {
  verse: number;
  /** Raw text content (for backward compatibility) */
  text: string;
  /** Parsed text segments with speaker attribution */
  segments: TextSegment[];
  /** Whether this verse starts a new paragraph */
  paragraphStart: boolean;
  /** Greek words with lemmas */
  greek: GreekWord[];
  /** Translation notes for this verse */
  notes: VerseNote[];
  /** Whether any part of this verse has a speaker tag */
  hasSpeaker: boolean;
}

export interface ParsedChapter {
  chapter: number;
  verses: ParsedVerse[];
}

export interface ParsedBook {
  id: string;
  name: string;
  chapters: ParsedChapter[];
}

/**
 * Parse an AIT XML string into a structured book object.
 */
export function parseAITXml(xmlContent: string): ParsedBook | null {
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(xmlContent, "text/xml");

    const bookEl = doc.getElementsByTagName("book")[0];
    if (!bookEl) return null;

    const bookId = bookEl.getAttribute("id") || "";
    const bookName = bookEl.getAttribute("name") || "";

    const chapters: ParsedChapter[] = [];
    const chapterEls = bookEl.getElementsByTagName("chapter");

    for (let i = 0; i < chapterEls.length; i++) {
      const chapterEl = chapterEls[i];
      const chapterNum = parseInt(chapterEl.getAttribute("num") || "0", 10);

      const verses: ParsedVerse[] = [];
      const verseEls = chapterEl.getElementsByTagName("verse");

      for (let j = 0; j < verseEls.length; j++) {
        const verseEl = verseEls[j];
        const verse = parseVerse(verseEl);
        if (verse) {
          verses.push(verse);
        }
      }

      chapters.push({ chapter: chapterNum, verses });
    }

    return { id: bookId, name: bookName, chapters };
  } catch (error) {
    console.error("Error parsing AIT XML:", error);
    return null;
  }
}

/**
 * Parse a single verse element.
 */
function parseVerse(verseEl: Element): ParsedVerse | null {
  const verseNum = parseInt(verseEl.getAttribute("num") || "0", 10);
  if (verseNum === 0) return null;

  // Parse text element
  const textEl = verseEl.getElementsByTagName("text")[0];
  const { text, segments, paragraphStart, hasSpeaker } = parseTextElement(textEl);

  // Parse Greek words
  const greek: GreekWord[] = [];
  const greekEl = verseEl.getElementsByTagName("greek")[0];
  if (greekEl) {
    const wordEls = greekEl.getElementsByTagName("w");
    for (let i = 0; i < wordEls.length; i++) {
      const wordEl = wordEls[i];
      greek.push({
        text: getTextContent(wordEl),
        lemma: wordEl.getAttribute("lemma") || "",
      });
    }
  }

  // Parse notes
  const notes: VerseNote[] = [];
  const noteEls = verseEl.getElementsByTagName("note");
  for (let i = 0; i < noteEls.length; i++) {
    const noteEl = noteEls[i];
    notes.push({
      term: noteEl.getAttribute("term") || "",
      explanation: getTextContent(noteEl),
    });
  }

  return {
    verse: verseNum,
    text,
    segments,
    paragraphStart,
    greek,
    notes,
    hasSpeaker,
  };
}

/**
 * Parse the <text> element, extracting plain text and speaker segments.
 */
function parseTextElement(textEl: Element | undefined): {
  text: string;
  segments: TextSegment[];
  paragraphStart: boolean;
  hasSpeaker: boolean;
} {
  if (!textEl) {
    return { text: "", segments: [], paragraphStart: false, hasSpeaker: false };
  }

  const segments: TextSegment[] = [];
  let plainText = "";
  let paragraphStart = false;
  let hasSpeaker = false;

  // Walk through child nodes
  const childNodes = textEl.childNodes;
  for (let i = 0; i < childNodes.length; i++) {
    const node = childNodes[i];

    if (node.nodeType === 3) {
      // Text node - strip markdown formatting
      const content = stripMarkdown(node.nodeValue || "");
      if (content.trim()) {
        segments.push({ type: "text", content });
        plainText += content;
      }
    } else if (node.nodeType === 1) {
      // Element node
      const el = node as Element;
      const tagName = el.tagName?.toLowerCase();

      if (tagName === "p") {
        // Paragraph marker
        paragraphStart = true;
      } else if (tagName === "q") {
        // Speaker quote
        const speaker = el.getAttribute("who") || "unknown";
        const content = getTextContent(el);
        segments.push({ type: "speaker", content, speaker });
        plainText += content;
        hasSpeaker = true;
      }
    }
  }

  return { text: plainText.trim(), segments, paragraphStart, hasSpeaker };
}

/**
 * Get text content of an element (handles nested elements).
 */
function getTextContent(el: Element): string {
  let text = "";
  const childNodes = el.childNodes;
  for (let i = 0; i < childNodes.length; i++) {
    const node = childNodes[i];
    if (node.nodeType === 3) {
      text += node.nodeValue || "";
    } else if (node.nodeType === 1) {
      text += getTextContent(node as Element);
    }
  }
  return stripMarkdown(text);
}

/**
 * Strip markdown formatting and speaker tag remnants from text.
 */
function stripMarkdown(text: string): string {
  // Remove **bold** markers
  text = text.replace(/\*\*([^*]+)\*\*/g, "$1");
  // Remove *italic* markers
  text = text.replace(/\*([^*]+)\*/g, "$1");
  // Remove leftover speaker tags [SPEAKER:...] and [/SPEAKER:...]
  text = text.replace(/\[\/SPEAKER:[^\]]*\]/g, "");
  text = text.replace(/\[SPEAKER:[^\]]*\]/g, "");
  return text;
}

/**
 * Get a specific verse from a parsed book.
 */
export function getVerseFromBook(
  book: ParsedBook,
  chapterNum: number,
  verseNum: number
): ParsedVerse | null {
  const chapter = book.chapters.find((c) => c.chapter === chapterNum);
  if (!chapter) return null;

  return chapter.verses.find((v) => v.verse === verseNum) || null;
}
