# AIT Bible XML format

Version 2.0

The files in `web/data/<book>.xml` are what the site reads. They are an export, not the source of truth: `translator/pipeline.py export` writes them from a run's validated chapter records in `translator/runs/`. Do not edit them by hand. To change the text, change the register or re-run chapters, then export again.

[ait-example.xml](ait-example.xml) holds three verses copied unchanged from the published data.

## Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ait version="2.0" run="20261118-162954-full-nt" model="claude-fable-5-2" register="0.4-draft">
  <book id="matthew" name="Matthew">
    <chapter num="6">
      <verse num="2">
        <text>…</text>
        <greek>…</greek>
        <note term="…" kind="…" lemma="…" traditional="…">…</note>
      </verse>
    </chapter>
  </book>
</ait>
```

Each file holds one book. Every verse in the Greek source appears exactly once, in order; the exporter refuses to write a book with a missing or invalid chapter.

## Elements

### `<ait>`

| Attribute | Description |
|---|---|
| `version` | Format version, `2.0`. |
| `run` | The run in `translator/runs/` this file was exported from. |
| `model` | The model that produced the run. |
| `register` | The decision register version the run used. |

### `<book>`

| Attribute | Description |
|---|---|
| `id` | Lowercase identifier with no spaces: `matthew`, `1corinthians`, `revelation`. Matches the file name. |
| `name` | Display name: `Matthew`, `1 Corinthians`. |

### `<chapter>`

| Attribute | Description |
|---|---|
| `num` | Chapter number. |

### `<verse>`

| Attribute | Description |
|---|---|
| `num` | Verse number, as numbered in SBLGNT. |
| `status` | Optional. Present only when SBLGNT brackets the verse: `double` (the whole verse is inside ⟦ ⟧, judged not original), `partial-double` (part of it is, as in Mark 16:8) or `single` (it contains words in [ ], judged doubtful). |

Contains one `<text>`, one `<greek>` and zero or more `<note>` elements.

### `<text>`

The English translation of the verse, as mixed content:

- **Plain text** is narration, or in a letter the author's own words.
- **`<p/>`** as the first child marks a verse that begins a new paragraph.
- **`<q who="…">`** wraps words spoken by someone. It is never nested: a verse is a flat sequence of narration and speaker segments. A speech that runs across verses is wrapped separately in each verse.

Quotation marks are part of the text. They open where a speech opens and close where it closes, so a verse in the middle of a long speech has none.

The joining space between two segments is written at the start of the following segment (`<q who="Jesus"> “Follow me.”</q>`), because the site's parser drops whitespace-only text between elements.

Bracket characters ⟦ ⟧ and [ ] in the text are carried over from SBLGNT and mark the same words they mark in the Greek.

#### Speaker values

| `who` | Meaning | Site styling |
|---|---|---|
| `Jesus` | Words spoken by Jesus, including when he quotes Scripture. | Red |
| `God` | Words spoken by God. | Purple |
| `angel` | Words spoken by an angel. | Blue |
| `scripture` | A quotation of Scripture introduced by the author or narrator. | None |
| `other` | Any other speaking character or group. | None |

Individual characters are not named.

### `<greek>`

The SBLGNT text of the verse, one `<w>` per word, in order.

| Attribute of `<w>` | Description |
|---|---|
| `lemma` | The dictionary form, from MorphGNT. |

The element content is the word as it appears in the text, with its punctuation and any SBLGNT brackets. The edition's text-critical sigla (⸀ ⸂ ⸃ and similar) are removed.

### `<note>`

A translator's note on the verse.

| Attribute | Description |
|---|---|
| `term` | The English phrase the note is about, as it appears in the verse. |
| `kind` | `departure` (the text departs from the mainstream English rendering), `register-exception` (the chapter deviated from the decision register), `ambiguity` (the Greek allows another reading), `textual` (a manuscript issue) or `background` (context a first-century reader had). |
| `lemma` | The Greek dictionary form the note concerns, or empty if it is not about one word. |
| `traditional` | The traditional English rendering, where there is one. |

The element content is the note text. It is plain prose with no markup.

## Encoding

Files are UTF-8. Greek is in Unicode, not transliterated. `&`, `<`, `>` and quotation marks in text and attributes are XML-escaped.

## Compatibility

The site's parser (`web/lib/xml-parser.ts`) reads `num`, `who`, `lemma` and `term` and ignores attributes it does not know, so the `status`, `kind`, `lemma` and `traditional` attributes added in 2.0 are available to the site but not yet displayed.

Version 1.0 allowed nested `<q>` elements and free-form speaker names, and had no provenance, status or note attributes.
