# AIT Bible Translator

AI translation of the Bible from original Greek, prioritizing accuracy and meaning over tradition.

---

## Setup

### 1. Install dependencies

```bash
pip install anthropic requests
```

If you get errors about the batch API, upgrade:

```bash
pip install --upgrade anthropic
```

### 2. Set your API key

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
echo 'export ANTHROPIC_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Get the Greek source texts

```bash
git clone https://github.com/morphgnt/sblgnt.git greek_texts
```

This downloads the MorphGNT SBLGNT (SBL Greek New Testament) with morphological tagging.

---

## Quick Start

**Translate one chapter (realtime):**

```bash
python translate.py --book matthew --chapter 6
```

**Translate entire book (batch, 50% cheaper):**

```bash
python translate_batch.py run --book matthew --model claude-opus-4-5 --thinking
```

---

## Two Ways to Translate

### Option A: Realtime (`translate.py`)

Translates chapters one at a time. Good for testing or small jobs.

```bash
# Single chapter
python translate.py --book matthew --chapter 6

# Specific verses
python translate.py --book matthew --chapter 6 --verses 1-18

# Entire book (sequential)
python translate.py --book matthew --all

# With extended thinking
python translate.py --book matthew --chapter 5 --thinking

# With Opus model
python translate.py --book matthew --chapter 5 --model claude-opus-4-5 --thinking
```

### Option B: Batch (`translate_batch.py`)

Submits all chapters at once. **50% cost savings.** Best for full books.

```bash
# Full pipeline: submit → wait → download
python translate_batch.py run --book matthew

# Or step by step:
python translate_batch.py submit --book matthew
python translate_batch.py status --book matthew
python translate_batch.py wait --book matthew      # optional: polls until done
python translate_batch.py download --book matthew
```

**You don't need to keep the terminal open.** After `submit`, close your laptop. Come back later and run `status` then `download`.

---

## Recommended Settings

For the best quality translation:

```bash
python translate_batch.py run --book matthew --model claude-opus-4-5 --thinking
```

| Flag                      | What it does                                                         |
| ------------------------- | -------------------------------------------------------------------- |
| `--model claude-opus-4-5` | Uses the most capable model                                          |
| `--thinking`              | Enables extended thinking for better reasoning on difficult passages |

**Cost estimate for Matthew (28 chapters) with Opus + thinking:**

- Realtime: ~$25-40
- Batch: ~$12-20 (50% off)

---

## All Options

### translate.py

```
--book, -b        Book name (required)
--chapter, -c     Chapter number
--verses, -v      Verse range, e.g., "1-18"
--all, -a         Translate all chapters
--model, -m       Model (default: claude-sonnet-4-5)
--thinking, -t    Enable extended thinking
--output, -o      Output directory (default: output/)
--greek-texts, -g Greek texts directory (default: greek_texts/)
--list-books      Show available books
```

### translate_batch.py

**Commands:**

- `submit` — Send batch to Anthropic
- `status` — Check progress
- `wait` — Poll until complete
- `download` — Save results to files
- `run` — Do all of the above

**Flags:**

```
--book, -b        Book name (required)
--model, -m       Model (default: claude-sonnet-4-5)
--thinking, -t    Enable extended thinking
--output, -o      Output directory (default: output/)
--greek-texts, -g Greek texts directory (default: greek_texts/)
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

## Available Books

```bash
python translate.py --list-books
```

```
matthew: 28 chapters      mark: 16 chapters
luke: 24 chapters         john: 21 chapters
acts: 28 chapters         romans: 16 chapters
1corinthians: 16          2corinthians: 13
galatians: 6              ephesians: 6
philippians: 4            colossians: 4
1thessalonians: 5         2thessalonians: 3
1timothy: 6               2timothy: 4
titus: 3                  philemon: 1
hebrews: 13               james: 5
1peter: 5                 2peter: 3
1john: 5                  2john: 1
3john: 1                  jude: 1
revelation: 22
```

---

## Export for Website

After translating, export to JSON for your Next.js app:

```bash
# Single book
python utils.py json output/matthew -o matthew.json

# All books
python utils.py export-all output -o json/
```

JSON format:

```json
{
  "book": "Matthew",
  "chapters": [
    {
      "chapter": 1,
      "verses": [
        { "verse": 1, "text": "..." },
        { "verse": 2, "text": "..." }
      ],
      "notes": "..."
    }
  ]
}
```

---

## Translation Philosophy

This translator follows these principles:

1. **Original Audience Understanding** — What would a first-century reader have understood?
2. **Accuracy Over Tradition** — Depart from familiar translations when they obscure meaning
3. **Meaning Over Brevity** — Use more words when needed to convey full meaning
4. **Critical Text Basis** — Uses SBLGNT, omits later additions (e.g., Lord's Prayer doxology)

Key translation examples:

- πραεῖς (Matthew 5:5) → "gentle in strength" (not "meek") — controlled strength, not weakness
- ὑποκριτής (Matthew 6:5) → "performers" (not "hypocrites") — theatrical critique, not moral inconsistency
- ἁπλοῦς (Matthew 6:22) → "generous" (not "single") — Hebrew idiom about disposition toward wealth
- λόγος (John 1:1) → "Logos" (not "Word") — reason, divine order, organizing principle of cosmos

---

## Troubleshooting

**"AttributeError: 'Messages' object has no attribute 'batches'"**

```bash
pip install --upgrade anthropic
```

**"ANTHROPIC_API_KEY environment variable not set"**

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**"Greek text file not found"**

```bash
git clone https://github.com/morphgnt/sblgnt.git greek_texts
```

**Batch stuck or want to cancel:**
The batch will auto-expire after 24 hours, or you can cancel via the Anthropic console.

---

## Files

```
translate.py          # Realtime translation (one chapter at a time)
translate_batch.py    # Batch translation (50% cheaper)
greek_parser.py       # Parses MorphGNT files
prompt_template.py    # The translation prompt
utils.py              # Export to JSON for website
requirements.txt      # Dependencies
```

---

## License

### Software Code
GNU GPL v3 - See [LICENSE](../LICENSE) for details. The code is free and open source, and any modifications must remain open source under GPL v3. This prevents proprietary forks.

### Translation Output
CC BY-NC-SA 4.0 - The English translations produced are licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0. Non-commercial use with attribution is permitted. Contact project maintainers for commercial licensing.

### Source Materials
- **SBLGNT Greek Text**: [CC BY 4.0](http://sblgnt.com/license/)
- **MorphGNT Data**: [CC BY-SA 3.0](https://github.com/morphgnt/sblgnt)
