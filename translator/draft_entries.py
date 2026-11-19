#!/usr/bin/env python3
"""
Draft register entries from a finished run.

    python draft_entries.py submit  --run RUN --lemma WORD [--lemma WORD ...]
    python draft_entries.py collect --run RUN
    python draft_entries.py score   --run RUN        # test drafts against the run

For each Greek word the model is shown every verse where it occurs, with the
Greek and the run's English, and decides whether the word needs one decision
for the whole New Testament. Words that vary correctly by sense get "no entry
needed". Drafts land in runs/RUN/drafts/; nothing touches register.json until
a human (or a reviewed script) merges them.

`score` checks each draft against the run it was drafted from, using the
validator's own matching: how many occurrences already match the proposed
forms. A run made without the entry is a register-off experiment for that
word, so the score says whether the model wavers (make it active), already
does this unaided (watch), or the entry's forms are incomplete (fix it).
"""

import argparse
import collections
import json
import sys
from pathlib import Path

from pipeline import (BOOK_TITLES, DEFAULT_MODEL, _patterns, get_client, load_manifest,
                      load_record, parse_custom_id, run_dir, segments_text)
from source import Source

SCHEMA = {
    "type": "object",
    "properties": {
        "needs_entry": {"type": "boolean"},
        "reason": {"type": "string"},
        "sense": {"type": "string"},
        "default": {"type": "string"},
        "alternates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "renderings": {"type": "array", "items": {"type": "string"}},
                    "when": {"type": "string"},
                },
                "required": ["renderings", "when"],
                "additionalProperties": False,
            },
        },
        "traditional": {"type": "string"},
        "status": {"type": "string", "enum": ["settled", "contested"]},
        "rationale": {"type": "string"},
        "standard_view": {"type": "string"},
        "watch": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["needs_entry", "reason", "sense", "default", "alternates", "traditional",
                 "status", "rationale", "standard_view", "watch"],
    "additionalProperties": False,
}

SYSTEM = """You maintain the decision register for the AIT Bible, an English translation of the Greek New Testament (SBLGNT).

The translation's stance: render what a competent first-century reader of Koine Greek would have understood, judged by usage in the period including the Septuagint, never by etymology. Depart from the traditional English word only where it now misleads a modern reader more than the alternative would; where the traditional word is still the best one, keep it. A departure must be one a lexicographer would accept.

Each chapter is translated in a separate request, so the translator cannot see how a word was rendered elsewhere. The register exists to fix that: it gives one decision per Greek word sense, applied to every chapter. An entry has a default rendering and, where needed, alternates with the condition under which each applies.

You will be given one Greek word and every verse of the New Testament where it occurs, with the Greek and the English from the latest run, which was made WITHOUT a register entry for this word. Decide whether the word needs an entry.

It needs an entry when competent translators would plausibly choose different English for the same sense, and the run shows it: the same sense rendered in different ways in different chapters, or rendered with a departure from tradition in some chapters and the traditional word in others.

It does NOT need an entry when the English varies only because the Greek word has several senses and each was rendered appropriately, or when the run is already consistent on the traditional word. Most common words do not need an entry. Say so plainly by setting needs_entry to false and explaining in "reason"; the other fields may then be empty.

When you write an entry:

- "sense": the meaning the entry governs, in a few words. If the entry governs only one sense of a broader word, say which.
- "default": the single English rendering for that sense, in dictionary form (singular noun, bare verb). Choose by the stance, not by majority vote of the run, though a rendering the run already favours is a point in its favour when the choice is close.
- "alternates": other renderings that are correct under a stated condition, each with the condition. Include here the word's OTHER senses that occur in the New Testament, so that the validator does not flag them: give the plain English renderings for each as a list of separate strings. Be complete: every occurrence in the list you are shown should be covered by the default or an alternate.
- "traditional": the usual rendering in the English tradition.
- "status": "contested" if scholars genuinely disagree and the default is an editorial choice; otherwise "settled".
- "rationale": two or three sentences on why this default, for a reader with no Greek.
- "standard_view": what mainstream translations and scholarship do, stated fairly, including when it differs from the default.
- "watch": other English renderings seen in the run for the governed sense, which the audit should count.

Renderings are plain strings, one rendering per string, with no parentheses, slashes or commentary. Do not cite a specific ancient source unless you are confident of it. Do not claim more than the evidence supports."""


def occurrences(run: str, lemma: str, src: Source):
    manifest = load_manifest(run)
    out = []
    for cid in manifest["chapters"]:
        rec = load_record(run, cid)
        book, chapter = parse_custom_id(cid)
        texts = {v["verse"]: segments_text(v["segments"]) for v in rec["parsed"]["verses"]}
        notes = [n for n in rec["parsed"]["notes"] if n["lemma"] == lemma]
        for sv in src.chapter(book, chapter):
            if lemma in sv.lemmas:
                out.append((f"{BOOK_TITLES[book]} {chapter}:{sv.verse}", sv.greek, texts[sv.verse],
                            [n for n in notes if n["verse"] == sv.verse]))
    return out


def build_params(run: str, lemma: str, src: Source, model: str) -> dict:
    occ = occurrences(run, lemma, src)
    lines = []
    for ref, greek, english, notes in occ:
        lines.append(f"{ref}\n  GREEK: {greek}\n  ENGLISH: {english}")
        for n in notes:
            lines.append(f"  NOTE ({n['kind']}, on “{n['phrase']}”): {n['note']}")
    user = (f"The Greek word is {lemma}. It occurs in {len(occ)} verses.\n\n"
            + "\n".join(lines)
            + "\n\nDecide whether this word needs a register entry, and if so write it.")
    return {
        "model": model,
        "max_tokens": 32000,
        "system": SYSTEM,
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA}},
    }


def drafts_dir(run: str) -> Path:
    d = run_dir(run) / "drafts"
    d.mkdir(exist_ok=True)
    return d


def cmd_submit(args):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    src = Source()
    lemmas = list(dict.fromkeys(args.lemma or []))
    if args.lemma_file:
        lemmas += [l for l in json.loads(Path(args.lemma_file).read_text(encoding="utf-8")) if l not in lemmas]
    if not lemmas:
        sys.exit("Give --lemma or --lemma-file.")
    requests = [Request(custom_id=f"draft-{i:03d}",
                        params=MessageCreateParamsNonStreaming(**build_params(args.run, lem, src, args.model)))
                for i, lem in enumerate(lemmas)]
    batch = get_client().messages.batches.create(requests=requests)
    (drafts_dir(args.run) / "batch.json").write_text(json.dumps(
        {"batch_id": batch.id, "model": args.model,
         "lemmas": {f"draft-{i:03d}": lem for i, lem in enumerate(lemmas)}}, ensure_ascii=False, indent=2))
    print(f"Submitted {len(requests)} drafting requests as batch {batch.id}.")


def cmd_collect(args):
    meta = json.loads((drafts_dir(args.run) / "batch.json").read_text(encoding="utf-8"))
    client = get_client()
    b = client.messages.batches.retrieve(meta["batch_id"])
    if b.processing_status != "ended":
        sys.exit(f"Batch is still {b.processing_status}.")
    tin = tout = 0
    for result in client.messages.batches.results(meta["batch_id"]):
        lemma = meta["lemmas"][result.custom_id]
        if result.result.type != "succeeded" or result.result.message.stop_reason != "end_turn":
            print(f"  {lemma}: FAILED ({result.result.type})")
            continue
        msg = result.result.message
        tin += msg.usage.input_tokens
        tout += msg.usage.output_tokens
        draft = json.loads("".join(blk.text for blk in msg.content if blk.type == "text"))
        draft["lemma"] = lemma
        (drafts_dir(args.run) / f"{result.custom_id}.json").write_text(
            json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  {lemma}: {'entry: ' + draft['default'] if draft['needs_entry'] else 'no entry needed'}")
    print(f"tokens: {tin:,} in, {tout:,} out")


def load_drafts(run: str):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(drafts_dir(run).glob("draft-*.json"))]


def score(run: str, draft: dict, src: Source) -> dict:
    """How the run (made without this entry) rendered the word, against the draft's forms."""
    default = _patterns([draft["default"]])
    alts = _patterns([r for a in draft["alternates"] for r in a["renderings"]])
    watch = {w: _patterns([w]) for w in draft["watch"]}
    counts = collections.Counter()
    seen = collections.Counter()
    for ref, greek, english, notes in occurrences(run, draft["lemma"], src):
        if any(p.search(english) for p in default):
            counts["default"] += 1
        elif any(p.search(english) for p in alts):
            counts["alternate"] += 1
        else:
            hit = next((w for w, ps in watch.items() if any(p.search(english) for p in ps)), None)
            counts["watch" if hit else "unmatched"] += 1
            if hit:
                seen[hit] += 1
    return {"counts": dict(counts), "watch_seen": dict(seen), "total": sum(counts.values())}


def cmd_score(args):
    src = Source()
    for d in load_drafts(args.run):
        if not d["needs_entry"]:
            print(f"{d['lemma']:<14} no entry: {d['reason'][:110]}")
            continue
        s = score(args.run, d, src)
        c = s["counts"]
        print(f"{d['lemma']:<14} default “{d['default']}” {c.get('default', 0)}, alternates {c.get('alternate', 0)}, "
              f"watch {c.get('watch', 0)} {s['watch_seen'] or ''}, unmatched {c.get('unmatched', 0)} of {s['total']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("submit"); p.add_argument("--run", required=True); p.add_argument("--lemma", action="append")
    p.add_argument("--lemma-file"); p.add_argument("--model", default=DEFAULT_MODEL); p.set_defaults(fn=cmd_submit)
    for name, fn in (("collect", cmd_collect), ("score", cmd_score)):
        p = sub.add_parser(name); p.add_argument("--run", required=True); p.set_defaults(fn=fn)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
