# AIT Bible Web

Next.js web application for the AIT Bible translation - a fresh translation from the original Greek, prioritizing accuracy and meaning over tradition.

## Features

- **Interactive Translation Viewer**: Browse books and chapters with clean, readable typography
- **Translation Carousel**: Homepage showcase comparing traditional translations with AIT translations
- **Vision Page**: Detailed explanation of the project's philosophy and translation approach
- **Dark Mode**: System-aware dark mode with manual toggle
- **Translation Notes**: Collapsible notes explaining significant translation decisions
- **Responsive Design**: Optimized for reading on all device sizes

## Setup

```bash
npm install
```

## Add Translation Data

1. Generate JSON from your translations using the translator tool:

```bash
cd /path/to/aitbible-translator
python utils.py json output/matthew -o matthew.json
```

2. Copy the JSON file to the `data/` folder:

```bash
cp matthew.json /path/to/aitbible-web/data/
```

The JSON format should be:

```json
{
  "book": "Matthew",
  "chapters": [
    {
      "chapter": 1,
      "verses": [
        { "verse": 1, "text": "The book of the genealogy..." },
        { "verse": 2, "text": "Abraham fathered Isaac..." }
      ],
      "notes": "**\"Term\" (v. 1)**: Explanation..."
    }
  ]
}
```

## Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Build for Production

```bash
npm run build
npm run start
```

## Project Structure

```
app/
  layout.tsx          # Root layout with header and footer
  providers.tsx       # Theme provider for dark mode (next-themes)
  page.tsx            # Home page with translation carousel and book list
  vision/
    page.tsx          # Vision page explaining project philosophy
  [book]/
    page.tsx          # Book page with chapter grid
    [chapter]/
      page.tsx        # Chapter page with translation and notes
components/
  Header.tsx          # Header with dark mode toggle
  TranslationNotes.tsx # Collapsible notes section with markdown support
  TranslationCarousel.tsx # Interactive carousel showcasing translation examples
lib/
  books.ts            # Book metadata (names, chapters, IDs)
  data.ts             # JSON data loading and book availability
data/
  matthew.json        # Translation files (Matthew, Mark, Luke, John)
  mark.json
  luke.json
  john.json
  ...
```

## Tech Stack

- **Next.js 16**: React framework with App Router
- **React 19**: Latest React features
- **TypeScript**: Type-safe development
- **Tailwind CSS 4**: Utility-first styling
- **next-themes**: Dark mode support with system preference detection
- **tailwindcss-animate**: Animation utilities

## Deploying

Works with Vercel, Netlify, or any Node.js host:

```bash
npm run build
```

For Vercel:

```bash
npx vercel
```
