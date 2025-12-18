# AIT Bible

AI-powered translation of the Bible from original Greek, prioritizing accuracy and meaning over tradition.

This project combines powerful AI translation capabilities with a modern web interface to make a fresh, thoughtful Bible translation accessible to everyone.

## What is AIT Bible?

AIT Bible uses Claude (Anthropic's AI) to translate the New Testament directly from the original Greek texts (SBLGNT). Unlike traditional translations constrained by committee decisions and ecclesiastical tradition, this translation aims to convey what the text would have meant to its original first-century audience.

**Key principles:**

- **Original Audience Understanding** — What would a first-century reader have understood?
- **Accuracy Over Tradition** — Depart from familiar translations when they obscure meaning
- **Meaning Over Brevity** — Use more words when needed to convey full meaning
- **Critical Text Basis** — Uses SBLGNT, omits later additions

## Project Components

This repository contains two main components:

### 1. Translator (`/translator`)

Python-based translation engine that uses Claude API to translate Greek texts.

**Features:**
- Real-time and batch translation modes
- 50% cost savings with batch API
- Extended thinking for complex passages
- Morphological Greek text parsing
- JSON export for web consumption

[→ See translator README for detailed usage](translator/readme.md)

### 2. Web App (`/web`)

Next.js application for browsing and reading the translations.

**Features:**
- Interactive translation viewer
- Translation notes with detailed explanations
- Dark mode support
- Translation carousel showcasing key passages
- Responsive design for all devices

[→ See web README for setup and deployment](web/readme.md)

## Quick Start

### Translate a Book

```bash
cd translator

# Install dependencies
pip install anthropic requests

# Set API key
export ANTHROPIC_API_KEY="your-api-key-here"

# Get Greek source texts
git clone https://github.com/morphgnt/sblgnt.git greek_texts

# Translate (batch mode recommended for cost savings)
python translate_batch.py run --book matthew --model claude-opus-4-5 --thinking
```

### Run the Web App

```bash
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the translation.

## Translation Examples

**Matthew 5:5** — "Gentle in strength" instead of "meek"

> Traditional: "Blessed are the **meek**, for they will inherit the earth."
>
> AIT: "Blessed are those **gentle in strength**, for they will inherit the earth."

The Greek *praeis* (πραεῖς) describes controlled strength, not weakness or passivity. Like a war horse trained for battle but responsive to its rider, it means having power but choosing restraint.

**Matthew 6:5** — "Performers" instead of "hypocrites"

> Traditional: "And when you pray, you must not be like the **hypocrites**."
>
> AIT: "And when you pray, do not be like the **performers**."

The Greek *hypokritēs* (ὑποκριτής) meant "stage actor"—not someone morally inconsistent, but someone putting on a theatrical performance for an audience.

**Matthew 6:22** — "Generous" instead of "single"

> Traditional: "If your eye is **single**, your whole body will be full of light."
>
> AIT: "If your eye is **generous**, your whole body will be full of light."

The Greek *haplous* (ἁπλοῦς) invokes a Hebrew idiom where a "good eye" means generosity and an "evil eye" means stinginess. In context with Matthew 6's teaching on treasure and Mammon, this is about one's disposition toward wealth, not physical vision.

**John 1:1** — "Logos" instead of "Word"

> Traditional: "In the beginning was the **Word**, and the Word was with God, and the Word was God."
>
> AIT: "In the beginning was the **Logos**, and the Logos was with God, and the Logos was God."

*Logos* (λόγος) carried meanings of reason, divine order, and the organizing principle of the cosmos, all nuances that "word" doesn't fully capture.

## Project Structure

```
aitbible/
├── translator/              # Python translation engine
│   ├── translate.py         # Real-time translation
│   ├── translate_batch.py   # Batch translation (50% cheaper)
│   ├── greek_parser.py      # Greek text parser
│   ├── prompt_template.py   # Translation prompt
│   └── utils.py             # Export to JSON
├── web/                     # Next.js web application
│   ├── app/                 # Next.js app router pages
│   ├── components/          # React components
│   ├── data/                # Translation JSON files
│   └── lib/                 # Utilities and data loading
└── README.md                # This file
```

## Workflow

1. **Translate** a book using the Python translator
2. **Export** the translation to JSON format
3. **Copy** JSON to the web app's data folder
4. **View** the translation in your browser

```bash
# 1. Translate
cd translator
python translate_batch.py run --book matthew --model claude-opus-4-5 --thinking

# 2. Export to JSON
python utils.py json output/matthew -o matthew.json

# 3. Copy to web app
cp matthew.json ../web/data/

# 4. View in browser
cd ../web
npm run dev
```

## Available Books

All 27 New Testament books are supported:

- **Gospels**: Matthew, Mark, Luke, John
- **History**: Acts
- **Paul's Letters**: Romans, 1-2 Corinthians, Galatians, Ephesians, Philippians, Colossians, 1-2 Thessalonians, 1-2 Timothy, Titus, Philemon
- **General Letters**: Hebrews, James, 1-2 Peter, 1-3 John, Jude
- **Apocalyptic**: Revelation

## Cost Estimates

Translating Matthew (28 chapters) with Claude Opus 4.5 + extended thinking:

- **Batch mode**: ~$12-20 (recommended)
- **Real-time mode**: ~$25-40

Batch mode provides 50% cost savings and is ideal for translating entire books.

## Technology

**Translator:**
- Python 3.x
- Anthropic Claude API (Opus 4.5 or Sonnet 4.5)
- MorphGNT SBLGNT Greek texts

**Web App:**
- Next.js 16
- React 19
- TypeScript
- Tailwind CSS 4
- next-themes for dark mode

## License

This project uses a dual-license approach:

### Software Code
**GNU GPL v3** - The code in this repository (Python scripts, web app, etc.) is licensed under the GNU General Public License v3.0. See [LICENSE](LICENSE) for details.

This means:
- ✅ You can use, modify, and distribute the code freely
- ✅ You can use it commercially
- ✅ **Any modifications must also be open source under GPL v3**
- ✅ Prevents proprietary forks - modifications must be shared back

This protects the project from being taken and commercialized without giving back to the community.

### Translation Output
**CC BY-NC-SA 4.0** - The English translation text produced by this software is licensed under [Creative Commons Attribution-NonCommercial-ShareAlike 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).

This means the translation text:
- ✅ Can be shared and adapted for non-commercial purposes
- ✅ Requires attribution to AIT Bible Project
- ✅ Derivatives must use the same license
- ❌ Cannot be used commercially without permission

For commercial licensing of translations, please contact the project maintainers.

### Source Materials
- **SBLGNT Greek Text**: [CC BY 4.0](http://sblgnt.com/license/) © 2010 Logos Bible Software and Society of Biblical Literature
- **MorphGNT Data**: [CC BY-SA 3.0](https://github.com/morphgnt/sblgnt)

## Learn More

- [Translator Documentation](translator/readme.md) — Detailed translation usage and options
- [Web App Documentation](web/readme.md) — Setup and deployment guide
- [Anthropic Claude](https://www.anthropic.com/claude) — The AI powering translations
- [SBLGNT](http://sblgnt.com/) — The Greek text source

## Vision

This project exists because traditional Bible translations often prioritize familiarity over accuracy. Words change meaning over centuries. "Hypocrite" once meant "actor," but now implies moral failing. "Let" once meant "prevent," but now means "allow."

By using AI trained on vast amounts of Greek literature and linguistic data, we can produce translations that better capture what the original authors intended their original audiences to understand — free from the constraints of tradition, committee politics, and theological agendas.

This is not a replacement for scholarly translation work, but a complement — a fresh perspective that invites readers to encounter familiar texts with new eyes.
