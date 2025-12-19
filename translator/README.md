Here is the raw README.md content. I have wrapped it in a code block so you can copy the whole thing easily.

Markdown

# AIT Bible Translator

AI translation of the Bible from original Greek, prioritizing accuracy and meaning over tradition. Supports **Anthropic Claude** and **Google Gemini** models.

---

## Setup

### 1. Install dependencies

```bash
pip install anthropic google-genai requests
```

If you get errors about the batch API or Gemini, upgrade:

```bash
pip install --upgrade anthropic google-genai
```

### 2. Set your API keys

You can use Anthropic (Claude), Google (Gemini), or both.

**Anthropic:**

```bash
export ANTHROPIC_API_KEY="your-anthropic-key-here"
```

**Google Gemini:**

```bash
export GEMINI_API_KEY="your-gemini-key-here"
```

_Tip: Add these lines to your shell profile (`~/.zshrc` or `~/.bashrc`) to save them permanently._

### 3. Get the Greek source texts

```bash
git clone [https://github.com/morphgnt/sblgnt.git](https://github.com/morphgnt/sblgnt.git) greek_texts
```

This downloads the MorphGNT SBLGNT (SBL Greek New Testament) with morphological tagging.

---

## Quick Start

**Translate one chapter (fast):**

```bash
python translate.py --book matthew --chapter 6
```

**Translate entire book (parallel processing):**

```bash
python translate.py --book matthew --all --model gemini-3-flash
```

**Translate the entire New Testament (bulk):**

```bash
python translate.py --new-testament --model gemini-3-flash --thinking
```

---

## Translation Modes

### 1. Realtime / Parallel (`translate.py`)

Best for single chapters, full books (fast), or the entire New Testament.

- **Fastest:** Uses threading to translate multiple chapters at once.
- **Models:** Supports both Claude and Gemini.

```bash
# Single chapter
python translate.py --book matthew --chapter 6

# Entire book (Parallel - finishes in seconds/minutes)
python translate.py --book matthew --all --model gemini-3-flash

# Full New Testament (Sequential books, parallel chapters)
python translate.py --new-testament --model gemini-3-flash --thinking
```

### 2. Batch (`translate_batch.py`)

Best for cost savings on large, non-urgent jobs. **50% cost savings.**

- **Slower:** Submits a file, waits for the provider to process it (up to 24h), then downloads results.
- **Cheaper:** Uses the Batch API pricing tiers.

```bash
# Full pipeline: submit → wait → download
python translate_batch.py run --book matthew --model claude-opus-4-5

# Or step by step:
python translate_batch.py submit --book matthew
python translate_batch.py status --book matthew
python translate_batch.py wait --book matthew      # polls until done
python translate_batch.py download --book matthew
```

---

## Recommended Settings

| Goal            | Command                              | Why?                                              |
| :-------------- | :----------------------------------- | :------------------------------------------------ |
| **Max Speed**   | `--model gemini-3-flash`             | Extremely fast, high rate limits, very cheap.     |
| **Max Quality** | `--model claude-opus-4-5 --thinking` | Deepest reasoning, best nuance.                   |
| **Balanced**    | `--model gemini-3 --thinking`        | Great reasoning at a lower price point than Opus. |

---

## All Options

### translate.py

```
--book, -b        Book name (required unless using --new-testament)
--chapter, -c     Chapter number
--verses, -v      Verse range, e.g., "1-18"
--all, -a         Translate all chapters in the book
--new-testament   Translate the entire New Testament (all books)
--model, -m       Model (default: gemini-3-flash)
--thinking, -t    Enable extended thinking
--output, -o      Output directory (default: output/)
--greek-texts, -g Greek texts directory (default: greek_texts/)
--parallel, -p    Number of parallel requests (default: 5 or auto)
--list-books      Show available books
```

### translate_batch.py

**Commands:** `submit`, `status`, `wait`, `download`, `run`

**Flags:**

```
--book, -b        Book name (required)
--model, -m       Model (default: gemini-3-flash)
--thinking, -t    Enable extended thinking
--output, -o      Output directory (default: output/)
--chapters        Specific chapters, e.g., "1-10" or "1,5,7"
--poll-interval   Seconds between status checks (default: 30)
--batch-id        Use specific batch ID instead of saved one
```

---

## Output

Translations are saved to:

```
output/
  matthew/
    chapter_01.txt
    chapter_02.txt
    ...
```

Each file contains:

1. The English translation with verse numbers
2. Translation notes explaining significant choices

---

## Export for Website

After translating, export to JSON for your Next.js app:

```bash
# Single book
python utils.py json output/matthew -o matthew.json

# All books
python utils.py export-all output -o json/
```

---

## Translation Philosophy

This translator follows these principles:

1. **Original Audience Understanding** — What would a first-century reader have understood?
2. **Accuracy Over Tradition** — Depart from familiar translations when they obscure meaning
3. **Meaning Over Brevity** — Use more words when needed to convey full meaning
4. **Critical Text Basis** — Uses SBLGNT, omits later additions (e.g., Lord's Prayer doxology)

Key translation examples:

- πραεῖς (Matthew 5:5) → "gentle in strength" (not "meek")
- ὑποκριτής (Matthew 6:5) → "performers" (not "hypocrites")
- ἁπλοῦς (Matthew 6:22) → "generous" (not "single")
- λόγος (John 1:1) → "Logos" (not "Word")

---

## Troubleshooting

**"ImportError: The 'google-genai' package is required..."**

```bash
pip install google-genai
```

**"AttributeError: 'Messages' object has no attribute 'batches'"**

```bash
pip install --upgrade anthropic
```

**"Rate limit hit..."**
The script will automatically retry. If it persists, try reducing parallelism:

```bash
python translate.py --book matthew --all --parallel 1
```

**Batch stuck or want to cancel:**
Batches auto-expire after 24 hours. You can cancel via the provider's console.

---

## Files

```
translate.py          # Realtime/Parallel translation
translate_batch.py    # Batch API translation (cheaper)
greek_parser.py       # Parses MorphGNT files
prompt_template.py    # The translation prompt
utils.py              # Export to JSON for website
requirements.txt      # Dependencies
```

---

## License

### Software Code

GNU GPL v3 - See [LICENSE](../LICENSE) for details. The code is free and open source.

### Translation Output

CC BY-NC-SA 4.0 - The English translations produced are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0.

### Source Materials

- **SBLGNT Greek Text**: [CC BY 4.0](http://sblgnt.com/license/)
- **MorphGNT Data**: [CC BY-SA 3.0](https://github.com/morphgnt/sblgnt)
