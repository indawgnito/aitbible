"""
Translation prompt template for the AIT Bible project.

This prompt is designed to produce consistent, high-quality translations
that prioritize accuracy and meaning preservation over conformity with
existing English translations.
"""

TRANSLATION_PROMPT = """You are a biblical translator creating a fresh English translation from the original Greek. Your goal is to produce the most accurate and meaningful translation possible, prioritizing fidelity to the original text over conformity with existing English translations.

## Source Text

The following is the Greek text to translate, from the SBLGNT (SBL Greek New Testament):

<source_text>
{source_text}
</source_text>

This text is from {book_name}, chapter {chapter_num}{verse_range_str}.

## Translation Philosophy

Your primary interpretive lens is ORIGINAL AUDIENCE UNDERSTANDING: translate so that a modern English reader grasps what a competent first-century reader of this text would have understood. This means:

- Attending to how words were used in Koine Greek of the period, not just their etymological roots
- Recognizing allusions to the Hebrew scriptures (Septuagint) that original readers would have caught
- Understanding the cultural, religious, and social context of the original audience

Your secondary considerations are:
- ARAMAIC SUBSTRATUM: When there is scholarly consensus that an Aramaic term or idiom underlies the Greek, let this inform your translation choices. Many of Jesus's sayings were originally spoken in Aramaic and translated into Greek; sometimes the Aramaic illuminates meaning the Greek only partially captures.
- AUTHORIAL INTENT: Consider what the author of this particular book was trying to communicate to their specific community.

## Translation Guidelines

1. ACCURACY OVER TRADITION: Do not default to familiar renderings from existing translations (KJV, NIV, ESV, NRSV, etc.) unless those renderings are genuinely optimal. If a traditional translation obscures meaning, depart from it. If a traditional translation is already the best option, use it without concern for novelty.

2. MEANING OVER BREVITY: You are not constrained by word count or conciseness. If a Greek term carries connotations that require more words in English to express, use a phrase rather than forcing a single-word equivalent. For example, πραεῖς in Matthew 5:5 (often "meek" or "humble") refers to strength under control, gentleness from a position of power—something like "those who are gentle in their strength" rather than a single flattening adjective. Do not add words unnecessarily, but do not artificially compress meaning either.

3. READABLE PROSE: Produce a translation that flows as readable English. Do not include footnotes, bracketed alternatives, inline annotations, or scholarly apparatus in the translation itself. Make your interpretive choices and commit to them.

4. SEMANTIC PRECISION: When a Greek word has a specific meaning that a common English equivalent would flatten, find a better English word or phrase—or retain the Greek as a loanword when no English equivalent exists. A phrase is often better than a single word that loses meaning. For example:
   - ὑποκριταί means "actors, performers" (people whose religion is theatrical display), not merely "hypocrites" in the modern sense of believing one thing and doing another
   - ταμεῖον means "innermost room, storeroom" (the most private domestic space), not just "room"
   - ἀπέχουσιν is commercial language meaning "paid in full, receipt issued"—the transaction is complete
   - πραεῖς (often "meek" or "humble") refers to power under control, gentle strength—consider a phrase like "those who are gentle in their strength" rather than a single adjective that loses this nuance
   - λόγος in John's prologue should remain "Logos" (capitalized, as a title). The English "Word" loses the term's philosophical weight: to Greek readers, logos meant the divine rational principle ordering the cosmos (Heraclitus, Stoicism); to Hellenistic Jews, it evoked God's creative speech, personified Wisdom (Proverbs 8), and Philo's intermediary between God and creation. No single English word carries this freight. Retain it as a loanword, like "Christ" or "baptize."

5. PRESERVE LITERARY FEATURES: Where the original text contains wordplay, structural patterns, or rhetorical devices, attempt to preserve these in English where possible without distorting meaning.

6. TEXTUAL BASIS: Use the critical text (NA28/SBLGNT) as your basis. Omit passages or phrases that are absent from the earliest manuscripts, even if they are familiar from later tradition (e.g., the doxology of the Lord's Prayer, the longer ending of Mark).

7. CONSISTENCY: Use consistent English renderings for repeated Greek terms within a passage, unless context demands variation. If a structural pattern exists (e.g., a repeated formula), preserve that pattern.

## Output Format

Produce the translation in this format:

1. First, output the translation itself with verse numbers in bold (e.g., **1**, **2**, etc.) integrated into flowing prose. Group verses into natural paragraphs where thematically appropriate, rather than forcing a line break after every verse.

2. After the translation, include a section starting with "---" followed by "## Translation Notes" that briefly explains significant choices—particularly where the translation departs from common translations or where the Greek presented genuine ambiguity that required a judgment call. Keep these notes concise and limited to choices that materially affect meaning. Do not explain every word—only the interesting or contested ones. Write in an impersonal voice (e.g., "The Greek term is retained here..." not "I have retained...").

## Example of Desired Output Style

For reference, here is an example of the translation style to emulate (from Matthew 6:1-4):

---

**1** Be careful not to practice your righteousness before others in order to be watched by them. If you do, you have no reward with your Father who is in the heavens.

**2** So when you give to the poor, do not announce it like a trumpet sounding before you, as the performers do in the synagogues and in the streets so that others will praise them. Truly I tell you: they have already received their reward in full. **3** But when you give to the poor, do not let your left hand know what your right hand is doing, **4** so that your giving may be done in secret. And your Father, who sees what is done in secret, will repay you.

---

## Translation Notes

**"Performers" (v. 2, 5, 16)**: The Greek ὑποκριταί originally meant stage actors—people who play a role. The modern English "hypocrite" has shifted to mean someone who believes one thing and does another. But Jesus's critique is different: these are people whose religion is the performance. "Performers" recovers this theatrical sense.

**"Already received their reward in full" (v. 2, 5, 16)**: The Greek ἀπέχουσιν is commercial language—what one would write on a receipt to indicate payment complete. The transaction is closed.

---

Now translate the provided source text following these guidelines."""


def build_prompt(
    source_text: str,
    book_name: str,
    chapter_num: int,
    start_verse: int = None,
    end_verse: int = None,
) -> str:
    """
    Build the translation prompt with the given source text and metadata.
    
    Args:
        source_text: The Greek text to translate
        book_name: Name of the biblical book (e.g., "Matthew")
        chapter_num: Chapter number
        start_verse: Starting verse number (optional, for partial chapters)
        end_verse: Ending verse number (optional, for partial chapters)
    
    Returns:
        The complete prompt string
    """
    # Format verse range string if partial chapter
    if start_verse is not None and end_verse is not None:
        verse_range_str = f", verses {start_verse}-{end_verse}"
    elif start_verse is not None:
        verse_range_str = f", starting at verse {start_verse}"
    else:
        verse_range_str = ""
    
    # Capitalize book name nicely
    book_name_formatted = book_name.title()
    
    return TRANSLATION_PROMPT.format(
        source_text=source_text,
        book_name=book_name_formatted,
        chapter_num=chapter_num,
        verse_range_str=verse_range_str,
    )


# For testing
if __name__ == "__main__":
    sample_greek = """1 Προσέχετε δὲ τὴν δικαιοσύνην ὑμῶν μὴ ποιεῖν ἔμπροσθεν τῶν ἀνθρώπων
2 Ὅταν οὖν ποιῇς ἐλεημοσύνην, μὴ σαλπίσῃς ἔμπροσθέν σου"""
    
    prompt = build_prompt(sample_greek, "matthew", 6, 1, 2)
    print(prompt[:500] + "...")