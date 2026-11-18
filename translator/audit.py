#!/usr/bin/env python3
"""
Audit the served translation (web/data/*.xml) against the Greek source.

    python audit.py                 # whole New Testament
    python audit.py --book mark     # one book
    python audit.py --data DIR      # audit a different data directory

Reports, in numbers: missing and extra verses, duplicate chapters, leftover
markup, speaker-tag damage, note coverage, and how consistently each
register lemma is rendered. Exit code is 1 if any structural check fails,
so it can gate a publish.
"""

import argparse
import collections
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from source import BOOKS, Source

ROOT = Path(__file__).resolve().parent
DEFAULT_DATA = ROOT.parent / "web" / "data"
REGISTER_PATH = ROOT / "register.json"

# Used for the drift table when no register exists yet.
FALLBACK_LEMMAS = {
    "ἐκκλησία": ["assembly", "ekklesia", "church", "congregation", "community"],
    "διάβολος": ["slanderer", "devil", "accuser"],
    "μετανοέω": ["repent", "change", "turn"],
    "δικαιοσύνη": ["justice", "righteousness"],
    "ὑποκριτής": ["performer", "hypocrite", "actor"],
}


_PATS = {}


def drift_pat(form):
    """Same inflection-tolerant matching the pipeline's validator uses."""
    if form not in _PATS:
        from pipeline import _stem_pattern
        _PATS[form] = _stem_pattern(form) or re.compile(r"(?!)")
    return _PATS[form]


def load_drift_lemmas():
    if REGISTER_PATH.exists():
        reg = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
        out = {}
        split = lambda forms: [p.strip().lower() for f in forms for p in f.split(" / ")]
        for e in reg["entries"]:
            forms = [e["default"]] + [a["rendering"] for a in e.get("alternates", [])]
            out[e["lemma"]] = split(forms) + [w.lower() for w in e.get("watch", [])]
            for lem, rendering in e.get("family", {}).items():
                out[lem] = split([rendering]) + [w.lower() for w in e.get("watch", [])]
        return out
    return FALLBACK_LEMMAS


def audit(data_dir: Path, books):
    src = Source()
    drift_lemmas = load_drift_lemmas()
    r = {
        "verses_source": 0, "verses_served": 0,
        "missing": [], "extra": [], "duplicate_chapters": [],
        "markup_in_text": [], "tag_remnants": [], "nested_speakers": 0,
        "jesus_under_other_speaker": 0, "notes": 0, "chapters_without_notes": [],
        "distinct_speakers": 0, "books_missing": [],
    }
    drift = {lem: collections.Counter() for lem in drift_lemmas}
    speakers = collections.Counter()

    for book in books:
        path = data_dir / f"{book}.xml"
        src_keys = {(c, v.verse) for c in src.chapters(book) for v in src.chapter(book, c)}
        r["verses_source"] += len(src_keys)
        if not path.exists():
            r["books_missing"].append(book)
            r["missing"] += [f"{book} {c}:{v}" for c, v in sorted(src_keys)]
            continue
        root = ET.parse(path).getroot()
        seen_ch = collections.Counter()
        served = collections.Counter()
        for ch in root.iter("chapter"):
            c = int(ch.get("num"))
            seen_ch[c] += 1
            ch_notes = 0
            for v in ch.findall("verse"):
                n = int(v.get("num"))
                served[(c, n)] += 1
                t = v.find("text")
                text = "".join(t.itertext()) if t is not None else ""
                ref = f"{book} {c}:{n}"
                if "**" in text or re.search(r"(?<![\w*])\*\w", text):
                    r["markup_in_text"].append(ref)
                if re.search(r"\[/?(JESUS|GOD|ANGEL|SCRIPTURE|CROWD|SPEAKER)", text):
                    r["tag_remnants"].append(ref)
                if t is not None:
                    top = [q for q in t if q.tag == "q"]
                    for q in t.iter("q"):
                        speakers[q.get("who")] += 1
                    if any(len(list(q.iter("q"))) > 1 for q in top):
                        r["nested_speakers"] += 1
                    if any(q.get("who") != "Jesus" and any(
                            i.get("who") == "Jesus" for i in q.iter("q") if i is not q)
                           for q in top):
                        r["jesus_under_other_speaker"] += 1
                ch_notes += len(v.findall("note"))
                g = v.find("greek")
                lemmas = {w.get("lemma") for w in g} if g is not None else set()
                low = text.lower()
                for lem in lemmas & drift.keys():
                    hits = [f for f in drift_lemmas[lem] if drift_pat(f).search(low)]
                    # forms are ordered default, alternates, watch: count the first that matches
                    for f in hits[:1] or ["(other)"]:
                        drift[lem][f] += 1
            r["notes"] += ch_notes
            if ch_notes == 0:
                r["chapters_without_notes"].append(f"{book} {c}")
        r["verses_served"] += len(served)
        r["duplicate_chapters"] += [f"{book} {c}" for c, k in seen_ch.items() if k > 1]
        r["missing"] += [f"{book} {c}:{v}" for c, v in sorted(src_keys - served.keys())]
        r["extra"] += [f"{book} {c}:{v}" for c, v in sorted(served.keys() - src_keys)]

    r["distinct_speakers"] = len(speakers)
    r["drift"] = {lem: dict(c.most_common()) for lem, c in drift.items() if c}
    return r


def report(r):
    def line(label, items, show=12):
        n = items if isinstance(items, int) else len(items)
        tail = ""
        if not isinstance(items, int) and items:
            tail = ": " + ", ".join(items[:show]) + (" …" if len(items) > show else "")
        print(f"  {label:<38}{n}{tail}")

    print("STRUCTURE")
    print(f"  {'verses in source / served':<38}{r['verses_source']} / {r['verses_served']}")
    line("books with no data", r["books_missing"])
    line("source verses not served", r["missing"])
    line("served verses not in source", r["extra"])
    line("duplicate chapters", r["duplicate_chapters"])
    print("TEXT")
    line("verses with markdown markup", r["markup_in_text"], 6)
    line("verses with speaker-tag remnants", r["tag_remnants"], 6)
    print("SPEAKERS")
    line("distinct speaker labels", r["distinct_speakers"])
    line("verses with nested speakers", r["nested_speakers"])
    line("Jesus quote under another speaker", r["jesus_under_other_speaker"])
    print("NOTES")
    line("notes", r["notes"])
    line("chapters with no notes", r["chapters_without_notes"], 6)
    print("RENDERING OF REGISTER LEMMAS (verses per rendering)")
    for lem, counts in r["drift"].items():
        print(f"  {lem:<16}" + ", ".join(f"{k} {v}" for k, v in counts.items()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--book", action="append", help="limit to this book (repeatable)")
    ap.add_argument("--data", type=Path, default=DEFAULT_DATA)
    ap.add_argument("--json", action="store_true", help="print the raw result as JSON")
    args = ap.parse_args()
    books = [b.lower() for b in args.book] if args.book else BOOKS
    r = audit(args.data, books)
    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        report(r)
    structural = (r["missing"] or r["extra"] or r["duplicate_chapters"] or r["markup_in_text"]
                  or r["tag_remnants"] or r["nested_speakers"] or r["books_missing"])
    sys.exit(1 if structural else 0)


if __name__ == "__main__":
    main()
