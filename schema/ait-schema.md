# AIT Bible XML Schema

Version 1.0

A custom XML format for storing Bible translation data with support for Greek source text, speaker attribution, and translation notes.

---

## Document Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ait version="1.0">
  <book id="matthew" name="Matthew">
    <chapter num="1">
      <verse num="1">
        <text>...</text>
        <greek>...</greek>
        <note term="...">...</note>
      </verse>
    </chapter>
  </book>
</ait>
```

---

## Elements Reference

### Root Element

#### `<ait>`

The root element containing the entire document.

| Attribute | Required | Description |
|-----------|----------|-------------|
| `version` | Yes | Schema version (currently `1.0`) |

```xml
<ait version="1.0">
  ...
</ait>
```

---

### Structure Elements

#### `<book>`

Container for a single book of the Bible.

| Attribute | Required | Description |
|-----------|----------|-------------|
| `id` | Yes | Lowercase identifier (e.g., `matthew`, `1corinthians`) |
| `name` | Yes | Display name (e.g., `Matthew`, `1 Corinthians`) |

```xml
<book id="matthew" name="Matthew">
  ...
</book>
```

#### `<chapter>`

Container for a single chapter.

| Attribute | Required | Description |
|-----------|----------|-------------|
| `num` | Yes | Chapter number (integer) |

```xml
<chapter num="5">
  ...
</chapter>
```

#### `<verse>`

Container for a single verse. Contains the translation, Greek source, and any notes.

| Attribute | Required | Description |
|-----------|----------|-------------|
| `num` | Yes | Verse number (integer) |

```xml
<verse num="3">
  <text>...</text>
  <greek>...</greek>
  <note term="...">...</note>
</verse>
```

---

### Content Elements

#### `<text>`

Contains the English translation text. May include inline elements for paragraph breaks and speaker attribution.

```xml
<text>
  <p/>Blessed are the poor in spirit, for theirs is the kingdom of heaven.
</text>
```

#### `<p/>`

Empty element marking a paragraph break. Placed inline within `<text>` before the first word of a new paragraph.

```xml
<text>
  <p/>This starts a new paragraph.
</text>
```

#### `<q>`

Quoted speech with speaker attribution. Used for red-letter text and other speaker identification.

| Attribute | Required | Description |
|-----------|----------|-------------|
| `who` | Yes | Speaker identifier (see Speaker Values below) |

```xml
<text>
  And he said to them, <q who="Jesus">"Follow me, and I will make you fishers of people."</q>
</text>
```

**Nesting:** `<q>` elements can be nested for quotes within quotes:

```xml
<text>
  <q who="Jesus">"You have heard that it was said, <q who="scripture">'Eye for eye, and tooth for tooth.'</q> But I tell you..."</q>
</text>
```

---

### Greek Elements

#### `<greek>`

Container for the Greek source text of a verse. Contains `<w>` elements for each word.

```xml
<greek>
  <w lemma="μακάριος">Μακάριοι</w>
  <w lemma="ὁ">οἱ</w>
  <w lemma="πτωχός">πτωχοὶ</w>
  ...
</greek>
```

#### `<w>`

A single Greek word with its dictionary form (lemma).

| Attribute | Required | Description |
|-----------|----------|-------------|
| `lemma` | Yes | Dictionary/base form of the word |

The element content is the inflected form as it appears in the text.

```xml
<w lemma="λέγω">λέγει</w>
```

---

### Note Elements

#### `<note>`

Translation note explaining a significant choice. Attached to a specific verse.

| Attribute | Required | Description |
|-----------|----------|-------------|
| `term` | No | The word or phrase being explained |

```xml
<note term="poor in spirit">
  The Greek πτωχοὶ τῷ πνεύματι refers to spiritual humility
  and recognition of one's need for God.
</note>
```

A verse may have multiple notes:

```xml
<verse num="5">
  <text>...</text>
  <greek>...</greek>
  <note term="meek">...</note>
  <note term="inherit the earth">...</note>
</verse>
```

---

### Reserved Elements (Future Use)

#### `<ref>`

Cross-reference to another passage. Not yet implemented.

| Attribute | Description |
|-----------|-------------|
| `target` | OSIS-style reference (e.g., `John.3.16`) |

```xml
<ref target="John.3.16">John 3:16</ref>
```

#### `<divine>`

Marks the divine name (tetragrammaton). Not yet implemented.

```xml
<divine>LORD</divine>
```

---

## Speaker Values

The `who` attribute on `<q>` elements uses these values:

| Value | Usage | Styling |
|-------|-------|---------|
| `Jesus` | Words of Christ | Red text |
| `God` | God the Father (voice from heaven, OT theophanies) | TBD |
| `angel` | Angelic messengers | TBD |
| `prophet` | OT prophets being quoted | TBD |
| `scripture` | Scripture quotations | TBD |
| `crowd` | Crowds, groups speaking | TBD |
| `narrator` | Editorial/narrative insertions | TBD |
| `{name}` | Named characters (e.g., `Peter`, `Pilate`) | TBD |

---

## Book Identifiers

Use these `id` values for the `<book>` element:

| ID | Name |
|----|------|
| `matthew` | Matthew |
| `mark` | Mark |
| `luke` | Luke |
| `john` | John |
| `acts` | Acts |
| `romans` | Romans |
| `1corinthians` | 1 Corinthians |
| `2corinthians` | 2 Corinthians |
| `galatians` | Galatians |
| `ephesians` | Ephesians |
| `philippians` | Philippians |
| `colossians` | Colossians |
| `1thessalonians` | 1 Thessalonians |
| `2thessalonians` | 2 Thessalonians |
| `1timothy` | 1 Timothy |
| `2timothy` | 2 Timothy |
| `titus` | Titus |
| `philemon` | Philemon |
| `hebrews` | Hebrews |
| `james` | James |
| `1peter` | 1 Peter |
| `2peter` | 2 Peter |
| `1john` | 1 John |
| `2john` | 2 John |
| `3john` | 3 John |
| `jude` | Jude |
| `revelation` | Revelation |

---

## Encoding

- All files must be UTF-8 encoded
- Greek text uses Unicode Greek characters (no transliteration)
- Standard XML escaping applies (`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`)

---

## Validation

A formal XSD or RelaxNG schema may be added in the future. For now, documents should:

1. Be well-formed XML
2. Have `<ait>` as root with `version="1.0"`
3. Use only elements defined in this specification
4. Include required attributes on all elements
5. Maintain proper nesting (verse inside chapter inside book inside ait)
