export interface BookInfo {
  id: string;
  name: string;
  chapters: number;
  testament: "old" | "new";
}

// New Testament books (what we're translating)
export const books: BookInfo[] = [
  { id: "matthew", name: "Matthew", chapters: 28, testament: "new" },
  { id: "mark", name: "Mark", chapters: 16, testament: "new" },
  { id: "luke", name: "Luke", chapters: 24, testament: "new" },
  { id: "john", name: "John", chapters: 21, testament: "new" },
  { id: "acts", name: "Acts", chapters: 28, testament: "new" },
  { id: "romans", name: "Romans", chapters: 16, testament: "new" },
  { id: "1corinthians", name: "1 Corinthians", chapters: 16, testament: "new" },
  { id: "2corinthians", name: "2 Corinthians", chapters: 13, testament: "new" },
  { id: "galatians", name: "Galatians", chapters: 6, testament: "new" },
  { id: "ephesians", name: "Ephesians", chapters: 6, testament: "new" },
  { id: "philippians", name: "Philippians", chapters: 4, testament: "new" },
  { id: "colossians", name: "Colossians", chapters: 4, testament: "new" },
  {
    id: "1thessalonians",
    name: "1 Thessalonians",
    chapters: 5,
    testament: "new",
  },
  {
    id: "2thessalonians",
    name: "2 Thessalonians",
    chapters: 3,
    testament: "new",
  },
  { id: "1timothy", name: "1 Timothy", chapters: 6, testament: "new" },
  { id: "2timothy", name: "2 Timothy", chapters: 4, testament: "new" },
  { id: "titus", name: "Titus", chapters: 3, testament: "new" },
  { id: "philemon", name: "Philemon", chapters: 1, testament: "new" },
  { id: "hebrews", name: "Hebrews", chapters: 13, testament: "new" },
  { id: "james", name: "James", chapters: 5, testament: "new" },
  { id: "1peter", name: "1 Peter", chapters: 5, testament: "new" },
  { id: "2peter", name: "2 Peter", chapters: 3, testament: "new" },
  { id: "1john", name: "1 John", chapters: 5, testament: "new" },
  { id: "2john", name: "2 John", chapters: 1, testament: "new" },
  { id: "3john", name: "3 John", chapters: 1, testament: "new" },
  { id: "jude", name: "Jude", chapters: 1, testament: "new" },
  { id: "revelation", name: "Revelation", chapters: 22, testament: "new" },
];

export function getBook(id: string): BookInfo | undefined {
  return books.find((b) => b.id === id.toLowerCase());
}

export function getBookName(id: string): string {
  return getBook(id)?.name ?? id;
}
