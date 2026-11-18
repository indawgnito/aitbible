#!/usr/bin/env python3
"""
Generate web/data/glossary.json from the decision register and a run.

    python build_glossary.py --run RUN            # writes web/data/glossary.json
    python build_glossary.py --run RUN --out FILE

The register is the single source of truth for rendering decisions; the
glossary is a view of it. An entry appears in the glossary when its default
rendering departs from the traditional English word, because those are the
words a reader will want explained. References are computed from the run:
"appearsIn" lists verses where the Greek word occurs and the rendering is
used, "greekAppearsIn" verses where the Greek word occurs and it is not.
"""

import argparse
import json
from pathlib import Path

from pipeline import (BOOK_TITLES, WEB_DATA, _patterns, load_manifest, load_record,
                      parse_custom_id, run_dir, segments_text)
from source import BOOKS, Source

CATEGORIES = {
    "departure": {
        "name": "Departures from tradition",
        "description": "Words where this translation uses a different English word from the traditional one, with the reason and the standard view.",
    },
    "loanword": {
        "name": "Names and titles left in Greek",
        "description": "Terms left untranslated because they work as a name or title and every English candidate would mislead.",
    },
}

LOANWORD_IDS = {"logos-prologue", "gehenna", "hades"}


def departs(entry: dict) -> bool:
    trad = entry["traditional"].lower()
    return not any(piece.strip().lower() in trad for piece in entry["default"].split(" / "))


def refs(pairs):
    """[(book, chapter, verse)] -> [{book, chapter, verses}] in canonical order."""
    grouped = {}
    for b, c, v in pairs:
        grouped.setdefault((b, c), []).append(v)
    return [{"book": b, "chapter": c, "verses": sorted(vs)}
            for (b, c), vs in sorted(grouped.items(), key=lambda kv: (BOOKS.index(kv[0][0]), kv[0][1]))]


def build(run: str) -> dict:
    register = json.loads((run_dir(run) / "register.json").read_text(encoding="utf-8"))
    manifest = load_manifest(run)
    src = Source()
    texts = {}
    for cid in manifest["chapters"]:
        rec = load_record(run, cid)
        if rec and rec["parsed"] and not rec["errors"]:
            book, chapter = parse_custom_id(cid)
            for v in rec["parsed"]["verses"]:
                texts[(book, chapter, v["verse"])] = segments_text(v["segments"])

    terms = []
    for e in register["entries"]:
        if not departs(e):
            continue
        pats = _patterns([e["default"]])
        scope = e.get("scope")
        used, other = [], []
        for (book, chapter, verse), text in texts.items():
            if scope and f"{book} {chapter}" not in scope:
                continue
            sv = next(v for v in src.chapter(book, chapter) if v.verse == verse)
            if e["lemma"] in sv.lemmas:
                (used if any(p.search(text) for p in pats) else other).append((book, chapter, verse))
        context = e["rationale"] + "\n\n" + "**The standard view.** " + e["standard_view"]
        if e["status"] == "contested":
            context += "\n\nScholars disagree on this word, and this rendering is an editorial choice."
        terms.append({
            "id": e["id"],
            "greek": e["lemma"],
            "lemma": e["lemma"],
            "aitRendering": e["default"],
            "traditional": e["traditional"],
            "category": "loanword" if e["id"] in LOANWORD_IDS else "departure",
            "brief": e["sense"][0].upper() + e["sense"][1:] + ".",
            "context": context,
            "appearsIn": refs(used),
            # An entry that governs only one sense of a common word (ἅγιος as
            # "holy ones", ἀπέχω on receipts) would list every other use here.
            "greekAppearsIn": [] if e.get("one_sense_only") else refs(other),
        })
    return {
        "generated_from": {"run": run, "register": register["version"], "model": manifest["model"]},
        "categories": CATEGORIES,
        "terms": terms,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", required=True)
    ap.add_argument("--out", type=Path, default=WEB_DATA / "glossary.json")
    args = ap.parse_args()
    glossary = build(args.run)
    args.out.write_text(json.dumps(glossary, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {len(glossary['terms'])} terms to {args.out}")
    examples = build_examples(args.run)
    (args.out.parent / "examples.json").write_text(json.dumps(examples, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {len(examples)} homepage examples to {args.out.parent / 'examples.json'}")


# ---------------------------------------------------------------- homepage examples

# The verses shown on the homepage: (book, chapter, verse, KJV words to mark,
# AIT words to mark). Everything else is read from the data at build time:
# both texts, and the translation's own note on the marked words. Nothing a
# visitor reads here is written by hand, so it cannot say more than the
# translation does.
EXAMPLES = [
    ("matthew", 16, 18, "church", "assembly"),
    ("matthew", 6, 2, "hypocrites", "performers"),
    ("matthew", 6, 22, "single", "generous"),
    ("matthew", 3, 2, "Repent", "Turn back"),
    ("john", 1, 1, "Word", "Logos"),
]


def build_examples(run: str) -> list:
    out = []
    for book, chapter, verse, trad_hl, ait_hl in EXAMPLES:
        ref = f"{BOOK_TITLES[book]} {chapter}:{verse}"
        rec = load_record(run, f"{book}-{chapter:03d}")
        ait = next(segments_text(v["segments"]) for v in rec["parsed"]["verses"] if v["verse"] == verse)
        kjv = json.loads((WEB_DATA / "kjv" / f"{BOOK_TITLES[book].replace(' ', '')}.json").read_text(encoding="utf-8"))
        trad = next(v["text"] for c in kjv["chapters"] if int(c["chapter"]) == chapter
                    for v in c["verses"] if int(v["verse"]) == verse)
        for text, hl, name in ((trad, trad_hl, "KJV"), (ait, ait_hl, "AIT")):
            if hl.lower() not in text.lower():
                raise SystemExit(f"{ref}: '{hl}' is not in the {name} text; fix EXAMPLES.")
        note = next((n for n in rec["parsed"]["notes"]
                     if n["verse"] == verse and ait_hl.lower() in n["phrase"].lower()), None)
        if note is None:
            raise SystemExit(f"{ref}: the translation has no note on '{ait_hl}'; pick another verse.")
        out.append({"reference": ref,
                    "href": f"/{book}/{chapter}#{verse}",
                    "chapterLabel": f"{BOOK_TITLES[book]} {chapter}",
                    "traditional": {"text": trad, "highlight": trad_hl},
                    "ait": {"text": ait, "highlight": ait_hl},
                    "note": {"term": note["phrase"], "text": note["note"]}})
    return out


if __name__ == "__main__":
    main()
