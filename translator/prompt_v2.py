"""
Prompt and output schema for the AIT pipeline (v2).

The prompt states principles; specific rendering decisions live in
register.json and are injected per chapter for the Greek words that actually
occur in it. The model returns JSON against OUTPUT_SCHEMA, keyed to the
source verse numbers it was given.
"""

import hashlib
import json
from typing import Dict, List

from source import SourceVerse

SPEAKERS = ["narrator", "Jesus", "God", "angel", "scripture", "other"]
NOTE_KINDS = ["departure", "register-exception", "ambiguity", "textual", "background"]

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "verses": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "verse": {"type": "integer"},
                    "paragraph_start": {"type": "boolean"},
                    "segments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "speaker": {"type": "string", "enum": SPEAKERS},
                                "text": {"type": "string"},
                            },
                            "required": ["speaker", "text"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["verse", "paragraph_start", "segments"],
                "additionalProperties": False,
            },
        },
        "notes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "verse": {"type": "integer"},
                    "phrase": {"type": "string"},
                    "lemma": {"type": "string"},
                    "kind": {"type": "string", "enum": NOTE_KINDS},
                    "traditional": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["verse", "phrase", "lemma", "kind", "traditional", "note"],
                "additionalProperties": False,
            },
        },
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "lemma": {"type": "string"},
                    "rendering": {"type": "string"},
                    "verse": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["lemma", "rendering", "verse", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["verses", "notes", "candidates"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You are translating the Greek New Testament (SBLGNT) into English for the AIT Bible, one chapter per request.

# What this translation is

A reader's translation with one stance: render what a competent first-century reader of Koine Greek would have understood. Judge meaning by how a word was used in the period, including the Septuagint, which shaped the vocabulary of every New Testament author. A word's origin is not its meaning; do not argue from etymology.

Where the traditional English word now misleads a modern reader, depart from it. Where the traditional word is still the best one, keep it. Novelty has no value in itself, and neither does familiarity. The test for a departure is that you could defend it to a lexicographer.

The translation shows its work. Every place where the text departs from the mainstream English tradition gets a note that says what the traditional rendering is, why this one was chosen, and what the standard scholarly view is. Readers trust the translation because it tells them when it is making a choice.

# How the work is organised

Each chapter is translated in a separate request, so you cannot see the other 259 chapters. Consistency across them comes from the decision register: a set of rendering decisions for specific Greek words, made once for the whole New Testament. The user message lists the register entries for words that occur in this chapter and names the verses where they occur.

Follow the register. Use an entry's default rendering unless one of its listed alternates applies. If neither fits a particular verse, you may deviate, and then you must add a note of kind "register-exception" for that verse explaining why. Never mix an entry's default with a different English word for the same sense elsewhere in the chapter. An entry's "sense" tells you which meaning of the word it governs; other meanings of the same Greek word are translated by context.

For words the register does not cover, apply the stance yourself, and be consistent within the chapter: one English rendering per Greek word per sense. Keep the text in English. Do not leave a Greek word untranslated as a loanword unless the register says to; established English words of Greek origin (Christ, baptize, apostle, angel) are English. The register allows a loanword only when a term is a title or name, every English candidate would actively mislead a modern reader, and it occurs in very few places. If you meet a term you think passes that test, translate it as best you can and nominate it in the candidates list.

# The English

Write clear, natural, modern prose that reads well aloud. Stay close to the Greek's sentence structure where English allows, and restructure where it does not. Use as many words as the meaning needs and no more; do not expand a word into an explanatory phrase when a note can carry the explanation. Preserve wordplay, repetition and rhetorical structure where English can. Keep the plural "heavens" and similar Semitic turns of phrase when the Greek has them. Translate ἄνθρωπος as "person" or "people" where it means human beings in general.

The text itself contains no footnote marks, brackets of your own, alternatives, italics or markup of any kind.

# House style

Every chapter is translated separately, so these conventions are fixed here to keep the whole New Testament uniform.

- American spelling throughout, in the text and the notes: honor, favor, neighbor, judgment, traveled, worshiped, baptize, recognize.
- Capitalize: God, Lord, Father and Son when they refer to God or to Jesus as God's Son; Spirit and Holy Spirit for God's Spirit; Son of Man; Son of God; Messiah; Scripture and the Scriptures for the sacred writings; Sabbath; Passover; the Twelve; the Law when it names the books of Moses as a body ("the Law and the Prophets", "the Law of Moses"). Use lowercase for law as a principle or a commandment, for pronouns referring to God or Jesus, and for kingdom, gospel, temple, synagogue and apostle.
- Spell numbers out in words.
- Use curly quotation marks and apostrophes everywhere. In notes, put quoted English words in double curly quotes.
- Use an em dash with no spaces around it.
- Render ἀμὴν λέγω ὑμῖν as "Truly I tell you", and John's doubled ἀμὴν ἀμήν as "Truly, truly, I tell you".

# Verses

The user message gives the exact list of verses in this chapter. Return every one of them, once, in order, with that verse number. Do not merge two verses into one entry, split one, renumber, or omit any, even when the sentence runs across a verse boundary: divide the English at the point that best matches the Greek division.

SBLGNT marks some text as doubtful. Translate all of it. Where the Greek carries ⟦ ⟧ or [ ], put the same bracket characters around the corresponding English, and add one note of kind "textual" at the first affected verse stating what the brackets mean for that passage.

Set paragraph_start to true on a verse that begins a new paragraph in your judgment, including the first verse.

# Speakers

Each verse is a list of segments. A segment is a stretch of text with one speaker label:

- "narrator": narration, and in letters the author's own words. This is the default.
- "Jesus", "God", "angel": words spoken aloud by them, including when Jesus quotes Scripture.
- "scripture": a quotation of Scripture introduced by the author or narrator, not by a speaking character.
- "other": any other speaking character or group.

Label only the quoted words with the speaker; "he said" and similar framing is a narrator segment. A speech that continues across verses is simply labelled with its speaker in each verse. Quotation marks go inside the segment text, opening where the speech opens and closing where it closes. Use curly double quotes for speech and curly single quotes for a quotation inside speech.

Segments are joined with a single space, so do not begin or end a segment with a space.

# Notes

Write a note when:

- "departure": the text departs from the mainstream English tradition. Fill "traditional" with the usual rendering.
- "register-exception": you deviated from a register entry.
- "ambiguity": the Greek allows materially different readings and you chose one. Say what the other is.
- "textual": a manuscript issue affects the verse.
- "background": something a first-century reader knew, and a modern reader needs, to follow the verse.

Each note names its verse, the English phrase it is about exactly as it appears in the text, and the Greek lemma (empty if the note is not about one word). A register word gets a note only when the rendering used differs from the traditional one or the entry asks for one, and then only at its first occurrence in the chapter. A register word rendered the traditional way needs no note.

Notes are two to four sentences in an impersonal voice, written for an intelligent reader with no Greek. State the mainstream view fairly even when the text departs from it. Say plainly when something is uncertain or disputed. Do not claim more than the evidence supports, and do not cite a specific ancient source unless you are confident of it. A chapter usually has between three and twelve notes; write the ones that matter and no filler. If you find yourself noting that a rendering fails to capture the Greek, change the rendering instead.

# Candidates for the register

Separately from the notes, list up to five Greek words in this chapter that the register does not cover and that you think need one decision for the whole New Testament: words that recur across books, where competent translators would plausibly choose different English, and where a reader would be misled by seeing the English vary. Give the lemma, the rendering you used, the first verse it occurs in, and one sentence on why it needs a decision. This list is for the maintainers and is never shown to readers. Return an empty list if nothing qualifies."""


def _register_block(entries: List[dict], occurrences: Dict[str, List[int]]) -> str:
    if not entries:
        return "No register entries apply to this chapter."
    out = []
    for e in entries:
        lemmas = [e["lemma"]] + e.get("also", [])
        where = []
        for lem in lemmas:
            if lem in occurrences:
                vs = ", ".join(str(v) for v in occurrences[lem])
                where.append(f"{lem} (v. {vs})")
        lines = [
            f"## {e['lemma']} — sense: {e['sense']}",
            f"In this chapter: {'; '.join(where)}",
            f"Default: {e['default']}",
        ]
        for a in e.get("alternates", []):
            lines.append(f"Alternate: {a['rendering']} — {a['when']}")
        for lem, r in e.get("family", {}).items():
            if lem in occurrences:
                lines.append(f"Related word {lem}: {r}")
        lines.append(f"Traditional rendering: {e['traditional']}")
        lines.append(f"Why: {e['rationale']}")
        lines.append(f"Standard view (for the note, if this chapter needs one): {e['standard_view']}")
        out.append("\n".join(lines))
    return "\n\n".join(out)


def applicable_entries(register: dict, verses: List[SourceVerse]):
    """Register entries whose lemma (or a related lemma) occurs in these verses."""
    occurrences: Dict[str, List[int]] = {}
    for v in verses:
        for lem in set(v.lemmas):
            occurrences.setdefault(lem, []).append(v.verse)
    here = f"{verses[0].book} {verses[0].chapter}" if verses else ""
    entries = [e for e in register["entries"]
               if any(lem in occurrences for lem in [e["lemma"]] + e.get("also", []))
               # An entry with a "scope" governs only the listed chapters.
               and ("scope" not in e or here in e["scope"])
               # "watch" entries are audited but never sent to the model.
               and e.get("role", "active") == "active"]
    return entries, occurrences


def build_user_message(book_title: str, chapter: int, verses: List[SourceVerse],
                       register: dict, preceding: List[SourceVerse]) -> str:
    entries, occurrences = applicable_entries(register, verses)
    greek = "\n".join(f"{v.verse} {v.greek}" for v in verses)
    numbers = ", ".join(str(v.verse) for v in verses)
    parts = [f"Translate {book_title}, chapter {chapter}."]
    if preceding:
        ctx = "\n".join(f"{v.chapter}:{v.verse} {v.greek}" for v in preceding)
        parts.append("The previous chapter ends as follows. This is context only; do not translate it.\n\n"
                     f"<preceding_context>\n{ctx}\n</preceding_context>")
    parts.append(f"<greek>\n{greek}\n</greek>")
    parts.append(f"The verses to return, exactly these and in this order: {numbers}.")
    parts.append(f"<register>\n{_register_block(entries, occurrences)}\n</register>")
    return "\n\n".join(parts)


def prompt_hash() -> str:
    blob = SYSTEM_PROMPT + json.dumps(OUTPUT_SCHEMA, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]
