#!/usr/bin/env python3
"""
Script to analyze the AIT Bible glossary and identify terms that may not add value.

CRITERIA FOR REMOVAL (remove if ANY apply):
1. Common English word with no significant translation nuance
2. The English rendering is self-explanatory and the brief doesn't reveal any surprising meaning
3. The term isn't theologically significant or doesn't represent a meaningful translation choice

CRITERIA TO KEEP (keep if ANY apply):
1. Loanwords retained from Greek (Logos, Messiah, Gehenna, etc.)
2. Theological terms with significant meaning
3. Terms where traditional translation is misleading
4. Idioms or phrases that need cultural context
5. Terms where the Greek has richer meaning than English captures
"""

import json
import re
from pathlib import Path

# Load the glossary
glossary_path = Path(__file__).parent.parent / "data" / "glossary.json"

with open(glossary_path, 'r', encoding='utf-8') as f:
    glossary = json.load(f)

terms = glossary["terms"]

# Words/patterns that indicate a term should be KEPT
KEEP_INDICATORS = [
    # Categories that are almost always valuable
    "loanword",  # Always keep loanwords

    # Key Greek terms that should always be kept
    "logos", "christos", "messiah", "gehenna", "ekklesia", "pistis", "dikaios",
    "pneuma", "sarx", "kosmos", "agape", "charis", "doxa", "kurios", "theos",
    "sozo", "metanoia", "basileia", "apostolos", "evangelion", "hagiasmos",
    "parousia", "mysterion", "koinonia", "parakletos",

    # Theological significance indicators in brief/context
    "messianic", "theological", "eschatological", "soteriological",
    "divine", "covenant", "atonement", "redemption", "salvation",
    "resurrection", "incarnation", "kingdom", "prophecy", "prophetic",
]

# Words/patterns that suggest a term MAY be removable (but needs careful review)
REMOVE_CANDIDATES = [
    # Simple everyday English words that may not need glossary entries
    # Only flag if the translation is obvious and brief doesn't reveal surprising meaning
]

# Specific IDs to KEEP regardless of other criteria (manual review showed these are valuable)
FORCE_KEEP = {
    "messiah-christos",
    "just-dikaios",
    "justice-dikaiosune",
    "assembly-kklesia",
    "gehenna-geenna",
    "logos-logos",
    "the-accuser-diabolos",
    "performer-pokrites",  # hypocrite etymology is valuable
    "turn-around-change-of-heart-metanoeo",  # repentance is major theological term
    "loving-kindness-charis",  # grace is major theological term
    "faithfulness-pistis",
    "world-system-kosmos",
    "i-am-emi",
    "the-adversary-satans",
    "nations-thnos",  # Gentiles distinction is important
    "place-of-atonement-lasterion",
    "liberation-polutrosis",
    "mature-teleios",  # perfect vs mature is significant
    "envoy-postolos",  # apostle meaning
    "herald-kerusso",  # preach meaning
    "toll-collector-telones",  # tax collector context
    "legal-scholar-grammateus",  # scribe role
    "skin-disease-lepros",  # leper context
    "sexual-immorality-porneia",
    "dwelling-tent-skene",  # tabernacle meaning
    "consecration-giasmos",
    "devotion-esebeia",
    "healthy-giaino",  # sound doctrine
    "impure-spirit-pnemakatharton",
    "act-of-power-dunamis",  # miracle meaning
    "do-homage-proskuneo",  # worship meaning
}

# Specific IDs to REMOVE (after manual review)
# These are common English words where the glossary entry doesn't add significant value
# Being CONSERVATIVE - only remove terms that clearly don't add value
FORCE_REMOVE = {
    # After careful review of the glossary, these terms meet removal criteria:
    # - Common English words where the brief/context doesn't reveal surprising meaning
    # - Or the traditional and AIT rendering are essentially the same
    # - Or the translation choice is minor and self-explanatory

    # ==========================================
    # Common English words with obvious meanings
    # ==========================================
    "cramped-thlibo",  # "Cramped" is self-explanatory common English
    "sensible-phronimos",  # "Sensible" is obvious, traditional "wise" is also clear
    "drunk-methusko",  # "Drunk" is a common word, context is obvious
    "noble-kalos",  # "Noble" / "good" - both clear English words
    "shattered-suntribo",  # "Shattered" / "broken" - both obvious
    "ordinary-chreos",  # "Ordinary" is self-explanatory
    "nonsense-lros",  # "Nonsense" / "idle tales" - both clear
    "fit-kanos",  # "Fit" / "worthy" - both common English
    "unjust-dikos",  # "Unjust" / "unrighteous" - both clear
    "raving-mad-mainomai",  # "Raving mad" / "mad" - both obvious
    "irrevocable-metameletos",  # "Irrevocable" is clear English
    "severity-potomia",  # "Severity" / "severity" - same word
    "futility-mataiotes",  # "Futility" / "vanity/futility" - traditional includes same word
    "thinking-phren",  # "Thinking" / "understanding" - both obvious

    # ==========================================
    # Where AIT and traditional are the same
    # ==========================================
    "give-glory-to-god-didomidoxa",  # AIT = traditional exactly

    # ==========================================
    # Minimal nuance terms
    # ==========================================
    "opportune-ekairos",  # "Opportune" / "Convenient/Opportune" - same meaning
    "authentic-lethinos",  # "Authentic" / "true" - minor nuance
    "transition-metabaino",  # "Transition" / "Depart" - minor nuance
    "leaping-up-llomai",  # "Leaping up" / "springing up" - same meaning
    "revealed-phaneroo",  # "Revealed" / "manifested" - both clear
    "pilfer-bastazo",  # "Pilfer" / "take" - both clear
    "bitterly-angry-cholao",  # "Bitterly angry" / "angry" - obvious intensifier
    "recover-szo",  # "Recover" / "be saved" - context-dependent, minor
    "petrified-poroo",  # "Petrified" / "hardened" - both work, minimal value

    # ==========================================
    # Duplicates with short IDs (likely errors or minimal entries)
    # ==========================================
    "rift",  # "Rift" / "division" - if exists, both are clear
    "noble",  # "Noble" / "good" - duplicate of noble-kalos if exists
    "bandit",  # "Bandit" / "robber" - both clear English
    "nullified",  # "Nullified" / "broken" - both clear

    # ==========================================
    # Very minor/specialized details
    # ==========================================
    "charcoal-fire-nthrakia",  # "Charcoal fire" / "fire" - minor detail

    # ==========================================
    # Essentially same translation
    # ==========================================
    "discerning-diakrino",  # "Discerning" / "discerning" - same word
}

def analyze_term(term):
    """Analyze a term and return recommendation with reasoning."""
    term_id = term["id"]
    category = term.get("category", "")
    ait_rendering = term.get("aitRendering", "")
    traditional = term.get("traditional", "")
    brief = term.get("brief", "")
    context = term.get("context", "")
    greek = term.get("greek", "")
    lemma = term.get("lemma", "")

    # Check force keep
    if term_id in FORCE_KEEP:
        return "KEEP", "Manually marked as essential term"

    # Check force remove
    if term_id in FORCE_REMOVE:
        return "REMOVE", "Manually identified as low-value term"

    # Always keep loanwords
    if category == "loanword":
        return "KEEP", "Loanword category - Greek term retained in English"

    # Always keep theological terms
    if category == "theological":
        return "KEEP", "Theological category - significant theological meaning"

    # Keep idioms (usually need cultural context)
    if category == "idiom":
        return "KEEP", "Idiom category - requires cultural context"

    # Keep textual variants
    if category == "textual-variant":
        return "KEEP", "Textual variant - manuscript evidence significance"

    # Check for key theological indicators in content
    combined_text = f"{brief} {context} {ait_rendering} {traditional}".lower()
    for indicator in KEEP_INDICATORS:
        if indicator.lower() in combined_text:
            return "KEEP", f"Contains theological indicator: {indicator}"

    # Check if AIT rendering differs significantly from traditional
    ait_lower = ait_rendering.lower().strip()
    trad_lower = traditional.lower().strip()

    # If they're essentially the same, might be removable
    if ait_lower == trad_lower:
        # But only if brief is short and obvious
        if len(brief) < 100 and not any(ind in combined_text for ind in ["first-century", "greek", "hebrew", "jewish", "roman", "cultural"]):
            return "REVIEW", "AIT same as traditional, brief is short"

    # Check for multi-word Greek phrases (usually idioms worth keeping)
    if " " in greek or len(greek) > 15:
        return "KEEP", "Multi-word Greek phrase - likely idiom or complex term"

    # Default: keep (be conservative)
    return "KEEP", "Default - no removal criteria met"

def main():
    results = {
        "KEEP": [],
        "REMOVE": [],
        "REVIEW": []
    }

    for term in terms:
        recommendation, reason = analyze_term(term)
        results[recommendation].append({
            "id": term["id"],
            "aitRendering": term.get("aitRendering", ""),
            "traditional": term.get("traditional", ""),
            "category": term.get("category", ""),
            "reason": reason
        })

    print("=" * 80)
    print("GLOSSARY ANALYSIS REPORT")
    print("=" * 80)
    print(f"\nTotal terms: {len(terms)}")
    print(f"KEEP: {len(results['KEEP'])}")
    print(f"REMOVE: {len(results['REMOVE'])}")
    print(f"REVIEW: {len(results['REVIEW'])}")

    print("\n" + "=" * 80)
    print("TERMS TO REMOVE")
    print("=" * 80)
    for item in results["REMOVE"]:
        print(f"\n- {item['id']}")
        print(f"  AIT: {item['aitRendering']}")
        print(f"  Traditional: {item['traditional']}")
        print(f"  Category: {item['category']}")
        print(f"  Reason: {item['reason']}")

    print("\n" + "=" * 80)
    print("TERMS TO REVIEW")
    print("=" * 80)
    for item in results["REVIEW"]:
        print(f"\n- {item['id']}")
        print(f"  AIT: {item['aitRendering']}")
        print(f"  Traditional: {item['traditional']}")
        print(f"  Category: {item['category']}")
        print(f"  Reason: {item['reason']}")

    # Output the IDs to remove
    print("\n" + "=" * 80)
    print("TERM IDS TO REMOVE (copy for removal script)")
    print("=" * 80)
    remove_ids = [item['id'] for item in results['REMOVE']]
    print(json.dumps(remove_ids, indent=2))

    return results

if __name__ == "__main__":
    main()
