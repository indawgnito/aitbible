#!/usr/bin/env python3
"""
Script to remove low-value terms from the AIT Bible glossary.
Creates a backup before making changes.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

# Terms to remove (identified via analysis)
TERMS_TO_REMOVE = [
    "leaping-up-llomai",
    "authentic-lethinos",
    "give-glory-to-god-didomidoxa",
    "transition-metabaino",
    "revealed-phaneroo",
    "opportune-ekairos",
    "petrified-poroo",
    "cramped-thlibo",
    "sensible-phronimos",
    "drunk-methusko",
    "bandit",
    "noble",
    "nullified",
    "rift",
    "pilfer-bastazo",
    "ordinary-chreos",
    "nonsense-lros",
    "fit-kanos",
    "bitterly-angry-cholao",
    "noble-kalos",
    "recover-szo",
    "charcoal-fire-nthrakia",
    "shattered-suntribo",
    "raving-mad-mainomai",
    "futility-mataiotes",
    "severity-potomia",
    "unjust-dikos",
    "discerning-diakrino",
    "thinking-phren",
    "irrevocable-metameletos",
]

def main():
    # Paths
    glossary_path = Path(__file__).parent.parent / "data" / "glossary.json"
    backup_dir = Path(__file__).parent.parent / "data" / "backups"

    # Create backup directory if needed
    backup_dir.mkdir(exist_ok=True)

    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"glossary_backup_{timestamp}.json"

    print(f"Creating backup at: {backup_path}")
    shutil.copy(glossary_path, backup_path)

    # Load glossary
    with open(glossary_path, 'r', encoding='utf-8') as f:
        glossary = json.load(f)

    original_count = len(glossary["terms"])
    print(f"Original term count: {original_count}")

    # Track what we remove
    removed_terms = []
    not_found = []

    # Filter terms
    new_terms = []
    for term in glossary["terms"]:
        if term["id"] in TERMS_TO_REMOVE:
            removed_terms.append({
                "id": term["id"],
                "aitRendering": term.get("aitRendering", ""),
                "traditional": term.get("traditional", "")
            })
        else:
            new_terms.append(term)

    # Check for terms that weren't found
    found_ids = {t["id"] for t in removed_terms}
    for term_id in TERMS_TO_REMOVE:
        if term_id not in found_ids:
            not_found.append(term_id)

    # Update glossary
    glossary["terms"] = new_terms

    # Save updated glossary
    with open(glossary_path, 'w', encoding='utf-8') as f:
        json.dump(glossary, f, indent=2, ensure_ascii=False)

    # Report
    print("\n" + "=" * 60)
    print("REMOVAL REPORT")
    print("=" * 60)
    print(f"Original terms: {original_count}")
    print(f"Terms removed: {len(removed_terms)}")
    print(f"Remaining terms: {len(new_terms)}")
    print(f"Terms not found: {len(not_found)}")

    if removed_terms:
        print("\n" + "-" * 60)
        print("REMOVED TERMS:")
        print("-" * 60)
        for term in removed_terms:
            print(f"  - {term['id']}")
            print(f"    AIT: {term['aitRendering']}")
            print(f"    Traditional: {term['traditional']}")

    if not_found:
        print("\n" + "-" * 60)
        print("TERMS NOT FOUND (may have different IDs):")
        print("-" * 60)
        for term_id in not_found:
            print(f"  - {term_id}")

    print("\n" + "=" * 60)
    print(f"Backup saved to: {backup_path}")
    print(f"Updated glossary saved to: {glossary_path}")
    print("=" * 60)

if __name__ == "__main__":
    main()
