"""
Glossary Builder for AIT Bible

Automatically extracts glossary candidates from translation outputs,
uses AI to generate full glossary entries, and merges into glossary.json.
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict
from google import genai

# Paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "output"
WEB_DATA_DIR = SCRIPT_DIR.parent / "web" / "data"
GLOSSARY_PATH = WEB_DATA_DIR / "glossary.json"


def parse_glossary_candidates(text: str) -> tuple[list[dict], list[dict]]:
    """
    Parse glossary candidates and enrichments from translation output.

    Expected formats:
    TERM: Logos | GREEK: λόγος | LEMMA: λόγος | TRADITIONAL: Word | CATEGORY: loanword
    ENRICH: λόγος | CONTEXT: In this passage, logos emphasizes...

    Returns:
        Tuple of (new_candidates, enrichments)
    """
    candidates = []
    enrichments = []

    # Find the glossary candidates section
    match = re.search(r'## Glossary Candidates\s*\n(.*?)(?=\n##|\Z)', text, re.DOTALL)
    if not match:
        return candidates, enrichments

    section = match.group(1)

    # Parse each TERM line (new terms)
    term_pattern = r'TERM:\s*([^|]+)\|\s*GREEK:\s*([^|]+)\|\s*LEMMA:\s*([^|]+)\|\s*TRADITIONAL:\s*([^|]+)\|\s*CATEGORY:\s*(\S+)'

    for m in re.finditer(term_pattern, section):
        candidates.append({
            'aitRendering': m.group(1).strip(),
            'greek': m.group(2).strip(),
            'lemma': m.group(3).strip(),
            'traditional': m.group(4).strip(),
            'category': m.group(5).strip().lower(),
        })

    # Parse each ENRICH line (enrichments to existing terms)
    enrich_pattern = r'ENRICH:\s*([^|]+)\|\s*CONTEXT:\s*(.+?)(?=\n(?:TERM:|ENRICH:)|\Z)'

    for m in re.finditer(enrich_pattern, section, re.DOTALL):
        enrichments.append({
            'lemma': m.group(1).strip(),
            'new_context': m.group(2).strip(),
        })

    return candidates, enrichments


def scan_translations_for_candidates() -> tuple[dict[str, dict], list[dict]]:
    """
    Scan all translation outputs and collect glossary candidates and enrichments.
    Returns:
        Tuple of (candidates dict keyed by lemma, list of enrichments)
    """
    candidates = defaultdict(lambda: {
        'aitRendering': None,
        'greek': None,
        'lemma': None,
        'traditional': None,
        'category': None,
        'appearsIn': [],
    })
    all_enrichments = []

    # Scan all book directories
    for book_dir in OUTPUT_DIR.iterdir():
        if not book_dir.is_dir():
            continue

        book_id = book_dir.name

        # Scan all chapter files
        for chapter_file in sorted(book_dir.glob("chapter_*.txt")):
            # Extract chapter number from filename
            match = re.search(r'chapter_(\d+)', chapter_file.name)
            if not match:
                continue

            chapter_num = int(match.group(1))

            # Read and parse
            text = chapter_file.read_text(encoding='utf-8')
            chapter_candidates, chapter_enrichments = parse_glossary_candidates(text)

            for cand in chapter_candidates:
                lemma = cand['lemma']

                # Update candidate info (use first occurrence's info)
                if candidates[lemma]['aitRendering'] is None:
                    candidates[lemma].update({
                        'aitRendering': cand['aitRendering'],
                        'greek': cand['greek'],
                        'lemma': lemma,
                        'traditional': cand['traditional'],
                        'category': cand['category'],
                    })

                # Track appearance (we'll refine verse numbers later from XML)
                appearance = {'book': book_id, 'chapter': chapter_num, 'verses': [1]}

                # Avoid duplicate chapter entries
                existing = [a for a in candidates[lemma]['appearsIn']
                           if a['book'] == book_id and a['chapter'] == chapter_num]
                if not existing:
                    candidates[lemma]['appearsIn'].append(appearance)

            # Collect enrichments with source info
            for enrich in chapter_enrichments:
                enrich['source_book'] = book_id
                enrich['source_chapter'] = chapter_num
                all_enrichments.append(enrich)

    return dict(candidates), all_enrichments


def generate_glossary_entries(candidates: dict[str, dict], batch_size: int = 15) -> list[dict]:
    """
    Use AI to generate full glossary entries with brief and context.
    Processes in batches to avoid response truncation.
    """
    if not candidates:
        return []

    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)

    all_entries = []
    candidate_items = list(candidates.items())

    # Process in batches
    for i in range(0, len(candidate_items), batch_size):
        batch = dict(candidate_items[i:i + batch_size])
        batch_num = i // batch_size + 1
        total_batches = (len(candidate_items) + batch_size - 1) // batch_size
        print(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} terms)...")

        entries = generate_batch_entries(client, batch)
        all_entries.extend(entries)

    return all_entries


def generate_batch_entries(client, candidates: dict[str, dict]) -> list[dict]:
    """Generate glossary entries for a single batch of candidates."""
    # Build prompt with batch candidates
    candidate_list = "\n".join([
        f"- {c['aitRendering']} ({c['greek']}, lemma: {c['lemma']}): "
        f"AIT uses \"{c['aitRendering']}\" instead of traditional \"{c['traditional']}\". "
        f"Category: {c['category']}"
        for c in candidates.values()
    ])

    prompt = f"""You are helping build a glossary for the AIT Bible translation.
For each term below, generate a glossary entry with:
1. A "brief" (1 sentence, ~15-20 words) explaining what the term means
2. A "context" (2-4 paragraphs) explaining why the AIT translation differs from traditional renderings

The context should:
- Explain what the Greek word meant to first-century readers
- Explain why the traditional English rendering may be inadequate
- Justify the AIT rendering choice
- Be written in an educational but accessible tone
- Use *asterisks* for Greek/foreign terms (for italics)

Here are the terms to process:

{candidate_list}

Output valid JSON array with this structure:
```json
[
  {{
    "lemma": "λόγος",
    "brief": "The divine Reason/Word — God's self-expression and the ordering principle of creation",
    "context": "For a first-century Greek reader, *logos* carried immense philosophical weight..."
  }}
]
```

Only output the JSON array, no other text."""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    # Parse response
    response_text = response.text.strip()

    # Extract JSON from response (handle markdown code blocks)
    json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group(1)

    try:
        entries = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"Error parsing AI response: {e}")
        print(f"Response was: {response_text[:500]}")
        return []

    # Merge AI-generated content with candidate data
    result = []
    for entry in entries:
        lemma = entry.get('lemma')
        if lemma and lemma in candidates:
            cand = candidates[lemma]
            result.append({
                'id': slugify(cand['aitRendering'], cand['lemma']),
                'greek': cand['greek'],
                'lemma': lemma,
                'aitRendering': cand['aitRendering'],
                'traditional': cand['traditional'],
                'category': cand['category'],
                'brief': entry.get('brief', ''),
                'context': entry.get('context', ''),
                'appearsIn': cand['appearsIn'],
            })

    return result


def process_enrichments(enrichments: list[dict], existing_glossary: dict) -> dict[str, str]:
    """
    Process enrichment suggestions using AI to merge new context into existing entries.

    Returns:
        Dict mapping lemma -> additional context paragraphs to append
    """
    if not enrichments:
        return {}

    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)

    # Index existing terms by lemma
    existing_by_lemma = {t['lemma']: t for t in existing_glossary.get('terms', [])}

    # Group enrichments by lemma
    enrichments_by_lemma = defaultdict(list)
    for e in enrichments:
        enrichments_by_lemma[e['lemma']].append(e)

    additions = {}

    for lemma, enrich_list in enrichments_by_lemma.items():
        if lemma not in existing_by_lemma:
            # Term doesn't exist yet, skip (it should be added as new term instead)
            continue

        existing_entry = existing_by_lemma[lemma]
        existing_context = existing_entry.get('context', '')

        # Combine all new context suggestions for this lemma
        new_contexts = "\n".join([
            f"- From {e['source_book']} {e['source_chapter']}: {e['new_context']}"
            for e in enrich_list
        ])

        prompt = f"""You are helping maintain a glossary for the AIT Bible translation.

The glossary already has an entry for "{existing_entry.get('aitRendering', lemma)}" ({lemma}):

EXISTING CONTEXT:
{existing_context}

New passages have been translated that use this term with potentially different nuances:

{new_contexts}

Your task:
1. Review the existing context and the new usage notes
2. Determine if the new usages add meaningful information not already covered
3. If yes, write 1-2 additional paragraphs to APPEND to the existing context (don't rewrite what's there)
4. If the existing context already covers these nuances adequately, respond with just: NO_UPDATE_NEEDED

Write any additional paragraphs in the same style as the existing context (educational, accessible, using *asterisks* for Greek terms).

Output ONLY the additional paragraphs to append, OR "NO_UPDATE_NEEDED". No other text."""

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            result = response.text.strip()

            if result and result != "NO_UPDATE_NEEDED":
                additions[lemma] = result
                print(f"  Enriching: {existing_entry.get('aitRendering', lemma)}")

        except Exception as e:
            print(f"  Error processing enrichment for {lemma}: {e}")

    return additions


def slugify(text: str, lemma: str = "") -> str:
    """Convert text to a URL-friendly slug, always including lemma for uniqueness."""
    slug = text.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')

    # Always append transliterated lemma to ensure uniqueness
    # (same English rendering can come from different Greek words)
    if lemma:
        lemma_slug = transliterate_greek(lemma)
        if lemma_slug:
            slug = f"{slug}-{lemma_slug}"

    return slug


def transliterate_greek(text: str) -> str:
    """Simple Greek to ASCII transliteration for slugs."""
    mapping = {
        'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e', 'ζ': 'z', 'η': 'e',
        'θ': 'th', 'ι': 'i', 'κ': 'k', 'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x',
        'ο': 'o', 'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't', 'υ': 'u',
        'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o',
        'ά': 'a', 'έ': 'e', 'ή': 'e', 'ί': 'i', 'ό': 'o', 'ύ': 'u', 'ώ': 'o',
        'ϊ': 'i', 'ϋ': 'u', 'ΐ': 'i', 'ΰ': 'u',
    }
    result = ""
    for char in text.lower():
        result += mapping.get(char, '')
    return result


def load_existing_glossary() -> dict:
    """Load existing glossary.json."""
    if GLOSSARY_PATH.exists():
        with open(GLOSSARY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'terms': [], 'categories': {}}


def merge_glossary(existing: dict, new_entries: list[dict]) -> dict:
    """
    Merge new entries into existing glossary.
    Updates existing entries, adds new ones.
    """
    # Index existing terms by lemma
    existing_by_lemma = {t['lemma']: t for t in existing.get('terms', [])}

    for entry in new_entries:
        lemma = entry['lemma']

        if lemma in existing_by_lemma:
            # Update existing entry - merge appearsIn
            old = existing_by_lemma[lemma]
            old_appearances = {(a['book'], a['chapter']) for a in old.get('appearsIn', [])}

            for appearance in entry['appearsIn']:
                key = (appearance['book'], appearance['chapter'])
                if key not in old_appearances:
                    old.setdefault('appearsIn', []).append(appearance)

            # Optionally update other fields if they were empty
            if not old.get('brief'):
                old['brief'] = entry['brief']
            if not old.get('context'):
                old['context'] = entry['context']
        else:
            # Add new entry
            existing_by_lemma[lemma] = entry

    # Rebuild terms list
    existing['terms'] = list(existing_by_lemma.values())

    # Ensure categories exist
    if 'categories' not in existing:
        existing['categories'] = {}

    default_categories = {
        'loanword': {
            'name': 'Loanwords',
            'description': 'Greek terms retained in English because no single word captures the full meaning'
        },
        'theological': {
            'name': 'Theological Terms',
            'description': 'Words where traditional translations carry theological baggage that may obscure the original sense'
        },
        'semantic-shift': {
            'name': 'Semantic Shifts',
            'description': 'English words that have changed meaning since early translations, now obscuring the Greek'
        },
        'idiom': {
            'name': 'Idioms & Expressions',
            'description': 'Phrases or expressions whose cultural context illuminates their meaning'
        },
        'textual-variant': {
            'name': 'Textual Variants',
            'description': 'Places where manuscript evidence suggests a different reading than traditional translations'
        }
    }

    for cat_id, cat_info in default_categories.items():
        if cat_id not in existing['categories']:
            existing['categories'][cat_id] = cat_info

    return existing


def save_glossary(glossary: dict):
    """Save glossary to glossary.json."""
    with open(GLOSSARY_PATH, 'w', encoding='utf-8') as f:
        json.dump(glossary, f, indent=2, ensure_ascii=False)
    print(f"Saved glossary to {GLOSSARY_PATH}")


def build_glossary():
    """Main function to build/update the glossary."""
    print("Scanning translations for glossary candidates...")
    candidates, enrichments = scan_translations_for_candidates()

    if not candidates and not enrichments:
        print("No glossary candidates or enrichments found.")
        return

    if candidates:
        print(f"Found {len(candidates)} unique terms:")
        for lemma, cand in candidates.items():
            print(f"  - {cand['aitRendering']} ({cand['greek']})")

    if enrichments:
        print(f"Found {len(enrichments)} enrichment suggestions.")

    # Load existing glossary to check what's new
    existing = load_existing_glossary()
    existing_lemmas = {t['lemma'] for t in existing.get('terms', [])}

    # Filter to only new candidates
    new_candidates = {k: v for k, v in candidates.items() if k not in existing_lemmas}

    # Update appearances for existing terms
    for lemma, cand in candidates.items():
        if lemma in existing_lemmas:
            for term in existing['terms']:
                if term['lemma'] == lemma:
                    old_appearances = {(a['book'], a['chapter']) for a in term.get('appearsIn', [])}
                    for appearance in cand['appearsIn']:
                        key = (appearance['book'], appearance['chapter'])
                        if key not in old_appearances:
                            term.setdefault('appearsIn', []).append(appearance)

    # Generate entries for new terms
    if new_candidates:
        print(f"\nGenerating entries for {len(new_candidates)} new terms...")
        new_entries = generate_glossary_entries(new_candidates)

        if new_entries:
            print(f"Generated {len(new_entries)} glossary entries.")
            existing = merge_glossary(existing, new_entries)

    # Process enrichments
    if enrichments:
        print(f"\nProcessing {len(enrichments)} enrichment suggestions...")
        additions = process_enrichments(enrichments, existing)

        if additions:
            print(f"Enriching {len(additions)} existing entries...")
            for term in existing['terms']:
                if term['lemma'] in additions:
                    # Append new context
                    existing_context = term.get('context', '')
                    new_context = additions[term['lemma']]
                    term['context'] = existing_context + "\n\n" + new_context

    # Save updated glossary
    save_glossary(existing)
    print(f"\nGlossary now has {len(existing['terms'])} terms.")


if __name__ == "__main__":
    build_glossary()
