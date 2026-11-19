#!/usr/bin/env python3
"""
Second-pass review: check a run's English against the Greek, verse by verse.

    python review.py seedtest --run RUN --model M [--effort E]   # can the reviewer find planted defects?
    python review.py submit   --run RUN [--model M] [--only book:ch]   # review by batch
    python review.py collect  --run RUN
    python review.py fix      --run RUN        # repair flagged verses, then re-review them
    python review.py report   --run RUN

The validator in pipeline.py proves every verse exists; it cannot tell whether
a verse says what the Greek says. The reviewer reads the Greek and the English
side by side and reports material problems only: omitted content, added
content, wrong meaning, or content placed in the wrong verse.

Findings are stored in the chapter record under "review". `fix` asks the
translation model to rewrite only the flagged verses, re-validates the chapter
and has the reviewer look again, for at most MAX_ROUNDS rounds.
"""

import argparse
import copy
import hashlib
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple

from pipeline import (BOOK_TITLES, PRICES, custom_id, get_client, load_manifest, load_record,
                      parse_custom_id, record_path, save_manifest, segments_text, validate)
from prompt_v2 import OUTPUT_SCHEMA, SYSTEM_PROMPT, build_user_message
from source import Source

# Chosen by the planted-defect test (seedtest) on run 20261118-162954-full-nt:
# Opus 5.5 and Fable 5.2 at medium effort both caught 24 of 24 with one stray
# finding; Sonnet 5.5 caught 23 with 19 stray findings; Haiku 5.5 caught 18.
# Opus is half the price and is a different model from the translator.
DEFAULT_REVIEW_MODEL = "claude-opus-5-5"
DEFAULT_REVIEW_EFFORT = "medium"
MAX_ROUNDS = 2

FINDING_TYPES = ["omission", "addition", "mistranslation", "wrong-verse"]

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "verse": {"type": "integer"},
                    "type": {"type": "string", "enum": FINDING_TYPES},
                    "severity": {"type": "string", "enum": ["major", "minor"]},
                    "greek": {"type": "string"},
                    "english": {"type": "string"},
                    "problem": {"type": "string"},
                },
                "required": ["verse", "type", "severity", "greek", "english", "problem"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["findings"],
    "additionalProperties": False,
}

REVIEW_SYSTEM = """You are checking an English translation of the Greek New Testament (SBLGNT) against the Greek, one chapter at a time. Your job is quality control for accuracy, not style.

For every verse, read the Greek and the English and ask whether the English says what the Greek says. Report a finding only for a material problem of one of these kinds:

- "omission": a Greek word, phrase or clause that carries meaning has no counterpart in the English of that verse.
- "addition": the English states something the Greek does not say or imply.
- "mistranslation": the English gives a wrong meaning: a wrong word sense, subject, object, number, tense, voice or negation, or a wrong name or figure.
- "wrong-verse": content belonging to one verse appears under another verse number.

Do NOT report:

- Wording you would have chosen differently when the English is a legitimate rendering.
- Deliberate departures from traditional renderings (for example "assembly" for ἐκκλησία, "turn back" for μετανοέω, "good news", "slave", "holy ones", "Logos", "brothers and sisters" for a mixed group). These are editorial decisions.
- Restructured sentences, Greek particles and conjunctions left untranslated where English does not need them, articles, or implied words supplied for English grammar.
- Matters of textual criticism. The English follows SBLGNT, including text in brackets.

Severity is "major" when a reader would be told something different from what the Greek says, or would miss something the Greek says. It is "minor" when the difference is real but small.

For each finding give the verse number, quote the Greek words concerned, quote the English words concerned (or the place where words are missing), and explain the problem in one or two sentences. Check every verse, including long ones, to the end. If the chapter has no material problems, return an empty list. Do not invent problems to have something to report, and do not list a verse only to say that it is acceptable: if on reflection there is no real problem, leave it out.

The message may list register decisions for words in this chapter. Those renderings, including the listed alternates, are settled and are never a finding."""


def review_prompt_hash() -> str:
    blob = REVIEW_SYSTEM + json.dumps(REVIEW_SCHEMA, sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def register_summary(register: Optional[dict], source_verses) -> str:
    """One line per register entry that applies to the chapter: lemma and its accepted renderings."""
    if not register:
        return ""
    from pipeline import entry_forms
    from prompt_v2 import applicable_entries
    active = {**register, "entries": [{**e, "role": "active"} for e in register["entries"]]}
    entries, _ = applicable_entries(active, source_verses)
    lines = []
    for e in entries:
        for lem, forms in entry_forms(e).items():
            if any(lem in sv.lemmas for sv in source_verses):
                lines.append(f"- {lem}: {'; '.join(forms)}")
    return "\n".join(lines)


def review_params(book: str, chapter: int, verses: List[dict], src: Source, model: str, effort: str,
                  register: Optional[dict] = None) -> dict:
    english = {v["verse"]: segments_text(v["segments"]) for v in verses}
    lines = []
    for sv in src.chapter(book, chapter):
        lines.append(f"{sv.verse}\n  GREEK: {sv.greek}\n  ENGLISH: {english.get(sv.verse, '(missing)')}")
    summary = register_summary(register, src.chapter(book, chapter))
    user = (f"{BOOK_TITLES[book]}, chapter {chapter}.\n\n" + "\n".join(lines)
            + (f"\n\nRegister decisions for words in this chapter:\n{summary}" if summary else "")
            + "\n\nReport the material problems, if any.")
    return {
        "model": model,
        "max_tokens": 32000,
        "system": REVIEW_SYSTEM,
        "messages": [{"role": "user", "content": user}],
        "output_config": {"effort": effort, "format": {"type": "json_schema", "schema": REVIEW_SCHEMA}},
    }


def parse_review(message) -> Tuple[Optional[List[dict]], str]:
    if message.stop_reason != "end_turn":
        return None, f"stop_reason={message.stop_reason}"
    raw = "".join(b.text for b in message.content if b.type == "text")
    try:
        return json.loads(raw)["findings"], ""
    except (json.JSONDecodeError, KeyError) as e:
        return None, f"unparseable: {e}"


def call_review(client, book, chapter, verses, src, model, effort, register=None):
    params = review_params(book, chapter, verses, src, model, effort, register)
    with client.messages.stream(**params) as stream:
        message = stream.get_final_message()
    findings, err = parse_review(message)
    usage = {"input_tokens": message.usage.input_tokens, "output_tokens": message.usage.output_tokens}
    return findings, err, usage


def run_register(run: str) -> dict:
    return json.loads((record_path(run, "x").parent.parent / "register.json").read_text(encoding="utf-8"))


def cost(usage: dict, model: str, batch: bool) -> float:
    price = PRICES.get(model)
    if not price:
        return 0.0
    return (usage["input_tokens"] * price[0] + usage["output_tokens"] * price[1]) / 1e6 * (0.5 if batch else 1)


# ---------------------------------------------------------------- seeded test

SEEDED = [("mark", 5), ("luke", 15), ("john", 11), ("acts", 9), ("romans", 8),
          ("1corinthians", 13), ("hebrews", 11), ("revelation", 5)]
CLEAN = [("matthew", 13), ("acts", 16), ("galatians", 3), ("james", 2)]
SWAPS = [("two", "three"), ("three", "two"), ("seven", "five"), ("twelve", "ten"), ("first", "second"),
         ("Peter", "John"), ("Jerusalem", "Galilee"), ("faith", "hope"), ("death", "life"),
         ("night", "day"), ("father", "brother"), ("heaven", "earth")]
ADDITIONS = [", and all who heard of it were amazed", ", just as he had promised long before",
             ", though none of them understood it"]


def plant(verses: List[dict], rng: random.Random) -> Tuple[List[dict], List[dict]]:
    """Return a damaged copy of the chapter and the list of planted defects."""
    out = copy.deepcopy(verses)
    planted = []
    used = set()
    order = list(range(len(out)))
    rng.shuffle(order)

    def last_seg(v):
        return max(range(len(v["segments"])), key=lambda i: len(v["segments"][i]["text"]))

    for i in order:  # omission: cut the final clause of a long verse
        v = out[i]
        s = v["segments"][last_seg(v)]
        m = re.match(r"^(.*[a-z]),\s+([^,]{25,90}?)([.;!?”’]*)$", s["text"], re.S)
        if m and len(s["text"].split()) >= 18:
            s["text"] = m.group(1) + (m.group(3) or ".")
            planted.append({"verse": v["verse"], "type": "omission", "detail": m.group(2)})
            used.add(i)
            break
    for i in order:  # addition: append an invented clause
        if i in used:
            continue
        v = out[i]
        s = v["segments"][-1]
        m = re.match(r"^(.*[a-z])([.!?][”’]*)$", s["text"], re.S)
        if m and len(s["text"].split()) >= 10:
            extra = rng.choice(ADDITIONS)
            s["text"] = m.group(1) + extra + m.group(2)
            planted.append({"verse": v["verse"], "type": "addition", "detail": extra})
            used.add(i)
            break
    for i in order:  # mistranslation: swap a word for a wrong one
        if i in used:
            continue
        v = out[i]
        done = False
        for a, b in SWAPS:
            for s in v["segments"]:
                if re.search(rf"\b{a}\b", s["text"]):
                    s["text"] = re.sub(rf"\b{a}\b", b, s["text"], count=1)
                    planted.append({"verse": v["verse"], "type": "mistranslation", "detail": f"{a} -> {b}"})
                    done = True
                    break
            if done:
                break
        if done:
            used.add(i)
            break
    return out, planted


def cmd_seedtest(args):
    src = Source()
    client = get_client()
    register = run_register(args.run)  # test the reviewer exactly as production uses it
    rng = random.Random(7)
    jobs = []
    for book, chapter in SEEDED + CLEAN:
        rec = load_record(args.run, custom_id(book, chapter))
        verses = rec["parsed"]["verses"]
        planted = []
        if (book, chapter) in SEEDED:
            verses, planted = plant(verses, rng)
        jobs.append((book, chapter, verses, planted))

    def work(job):
        book, chapter, verses, planted = job
        findings, err, usage = call_review(client, book, chapter, verses, src, args.model, args.effort, register)
        return job, findings, err, usage

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(work, jobs))

    hit = total = 0
    extra_seeded = extra_clean = 0
    spend = 0.0
    out = []
    for (book, chapter, verses, planted), findings, err, usage in results:
        spend += cost(usage, args.model, batch=False)
        if findings is None:
            print(f"  {book} {chapter}: reviewer failed ({err})")
            continue
        planted_verses = {p["verse"] for p in planted}
        found = {f["verse"] for f in findings}
        caught = [p for p in planted if p["verse"] in found]
        missed = [p for p in planted if p["verse"] not in found]
        others = [f for f in findings if f["verse"] not in planted_verses]
        hit += len(caught)
        total += len(planted)
        if planted:
            extra_seeded += len(others)
        else:
            extra_clean += len(others)
        print(f"  {book} {chapter}: planted {len(planted)}, caught {len(caught)}"
              + (f", MISSED {[(p['verse'], p['type']) for p in missed]}" if missed else "")
              + f", other findings {len(others)}")
        out.append({"book": book, "chapter": chapter, "planted": planted, "findings": findings})
    print(f"{args.model} at effort {args.effort}: caught {hit} of {total} planted defects; "
          f"{extra_seeded} other findings in the 8 damaged chapters, {extra_clean} in the 4 untouched ones; "
          f"cost ${spend:.2f} real time for 12 chapters")
    path = record_path(args.run, "x").parent.parent / f"seedtest-{args.model}-{args.effort}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"details: {path}")


# ---------------------------------------------------------------- batch review

def cmd_submit(args):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    manifest = load_manifest(args.run)
    src = Source()
    register = run_register(args.run)
    wanted = None
    if args.only:
        wanted = {custom_id(o.split(":")[0].lower(), int(o.split(":")[1])) for o in args.only}
    requests = []
    for cid in manifest["chapters"]:
        if wanted and cid not in wanted:
            continue
        rec = load_record(args.run, cid)
        if rec is None or rec["errors"]:
            continue
        book, chapter = parse_custom_id(cid)
        requests.append(Request(custom_id=cid, params=MessageCreateParamsNonStreaming(
            **review_params(book, chapter, rec["parsed"]["verses"], src, args.model, args.effort, register))))
    if not args.yes:
        print(f"About to submit {len(requests)} review requests on {args.model} (effort {args.effort}).")
        if input("Type 'yes' to submit: ").strip().lower() != "yes":
            sys.exit("Cancelled.")
    batch = get_client().messages.batches.create(requests=requests)
    manifest["review"] = {"batch_id": batch.id, "model": args.model, "effort": args.effort,
                          "prompt_hash": review_prompt_hash(), "chapters": len(requests)}
    save_manifest(args.run, manifest)
    print(f"Submitted {len(requests)} review requests as batch {batch.id}.")


def store_review(run: str, cid: str, findings, usage, model, effort, batch: bool, round_: int, error: str = ""):
    rec = load_record(run, cid)
    history = rec.get("review_history", [])
    if "review" in rec:
        history.append(rec["review"])
    rec["review_history"] = history
    rec["review"] = {"model": model, "effort": effort, "prompt_hash": review_prompt_hash(),
                     "round": round_, "batch": batch, "usage": usage,
                     "findings": findings if findings is not None else [], "error": error}
    record_path(run, cid).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")


def cmd_collect(args):
    manifest = load_manifest(args.run)
    rv = manifest["review"]
    client = get_client()
    b = client.messages.batches.retrieve(rv["batch_id"])
    if b.processing_status != "ended":
        sys.exit(f"Review batch is still {b.processing_status}.")
    failed = 0
    for result in client.messages.batches.results(rv["batch_id"]):
        if result.result.type != "succeeded":
            failed += 1
            store_review(args.run, result.custom_id, None, {"input_tokens": 0, "output_tokens": 0},
                         rv["model"], rv["effort"], True, 1, error=result.result.type)
            continue
        msg = result.result.message
        findings, err = parse_review(msg)
        failed += findings is None
        store_review(args.run, result.custom_id, findings,
                     {"input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens},
                     rv["model"], rv["effort"], True, 1, error=err)
    print(f"Collected reviews; {failed} failed.")
    cmd_report(args)


# ---------------------------------------------------------------- fixing

FIX_INSTRUCTIONS = """A reviewer compared your translation of this chapter with the Greek and reported the problems below. For each one, decide whether the reviewer is right. If so, correct the verse. If the reviewer is mistaken, leave the verse as it is.

Return ONLY the verses listed here, each in full, in the same JSON format as before. Do not change any other verse. In "notes", return the complete set of notes for those verses as they should now read: keep a note that still fits, and rewrite any note whose quoted phrase or explanation no longer matches the corrected text. Return an empty candidates list.

Verses to return: {verses}

Your current translation of those verses:
{current}

Your current notes on those verses:
{notes}

Reviewer findings:
{findings}"""


def fix_chapter(client, run: str, cid: str, src: Source, register: dict, manifest: dict) -> dict:
    rec = load_record(run, cid)
    book, chapter = parse_custom_id(cid)
    findings = [f for f in rec["review"]["findings"] if f["severity"] == "major"]
    numbers = sorted({f["verse"] for f in findings})
    by_num = {v["verse"]: v for v in rec["parsed"]["verses"]}
    numbers = [n for n in numbers if n in by_num]
    source_verses = src.chapter(book, chapter)
    base = build_user_message(BOOK_TITLES[book], chapter, source_verses, register, [])
    user = base + "\n\n" + FIX_INSTRUCTIONS.format(
        verses=", ".join(map(str, numbers)),
        current="\n".join(f"{n} {segments_text(by_num[n]['segments'])}" for n in numbers),
        notes="\n".join(f"- verse {x['verse']}, on “{x['phrase']}” ({x['kind']}): {x['note']}"
                        for x in rec["parsed"]["notes"] if x["verse"] in numbers) or "(none)",
        findings="\n".join(f"- verse {f['verse']} ({f['type']}): Greek «{f['greek']}», English «{f['english']}». {f['problem']}"
                           for f in findings))
    params = {"model": manifest["model"], "max_tokens": 32000, "system": SYSTEM_PROMPT,
              "messages": [{"role": "user", "content": user}],
              "output_config": {"effort": manifest["effort"],
                                "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}}}
    with client.messages.stream(**params) as stream:
        message = stream.get_final_message()
    usage = {"input_tokens": message.usage.input_tokens, "output_tokens": message.usage.output_tokens}
    result = {"usage": usage, "changed": [], "error": ""}
    if message.stop_reason != "end_turn":
        result["error"] = f"stop_reason={message.stop_reason}"
        return result
    reply = json.loads("".join(b.text for b in message.content if b.type == "text"))
    returned = {v["verse"]: v for v in reply["verses"]}
    new_parsed = copy.deepcopy(rec["parsed"])
    for v in new_parsed["verses"]:
        r = returned.get(v["verse"])
        if v["verse"] in numbers and r and segments_text(r["segments"]) != segments_text(v["segments"]):
            result["changed"].append({"verse": v["verse"], "before": segments_text(v["segments"]),
                                      "after": segments_text(r["segments"])})
            v["segments"] = r["segments"]
    changed_verses = {c["verse"] for c in result["changed"]}
    if changed_verses:
        # Notes on a rewritten verse are replaced by the fixer's notes for it, in place.
        fresh = [n for n in reply.get("notes", []) if n["verse"] in changed_verses]
        kept = [n for n in new_parsed["notes"] if n["verse"] not in changed_verses]
        new_parsed["notes"] = sorted(kept + fresh, key=lambda n: n["verse"])
        result["notes_replaced"] = len(fresh)
    errors, warnings = validate(new_parsed, source_verses, register)
    if errors:
        result["error"] = "fix failed validation: " + errors[0]
        return result
    rec["parsed"] = new_parsed
    rec["warnings"] = warnings
    rec.setdefault("fixes", []).append({"round": rec["review"]["round"], "model": manifest["model"],
                                        "usage": usage, "changed": result["changed"]})
    record_path(run, cid).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return result


def cmd_fix(args):
    manifest = load_manifest(args.run)
    rv = manifest["review"]
    src = Source()
    register = run_register(args.run)
    client = get_client()
    for round_ in range(1, MAX_ROUNDS + 1):
        todo = []
        for cid in manifest["chapters"]:
            rec = load_record(args.run, cid)
            rev = rec.get("review")
            if rev and rev["round"] == round_ and any(f["severity"] == "major" for f in rev["findings"]) \
                    and len(rec.get("fixes", [])) < round_:
                todo.append(cid)
        if not todo:
            break
        print(f"Round {round_}: fixing {len(todo)} chapters with major findings.")

        def work(cid):
            res = fix_chapter(client, args.run, cid, src, register, manifest)
            if res["error"]:
                return cid, res, None
            rec = load_record(args.run, cid)
            book, chapter = parse_custom_id(cid)
            findings, err, usage = call_review(client, book, chapter, rec["parsed"]["verses"], src,
                                               rv["model"], rv["effort"], register)
            store_review(args.run, cid, findings, usage, rv["model"], rv["effort"], False, round_ + 1, error=err)
            return cid, res, findings

        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            for cid, res, findings in pool.map(work, todo):
                left = "?" if findings is None else sum(f["severity"] == "major" for f in findings)
                print(f"  {cid}: {res['error'] or str(len(res['changed'])) + ' verses changed'}; "
                      f"major findings after re-review: {left}")
    cmd_report(args)


def cmd_report(args):
    manifest = load_manifest(args.run)
    reviewed = clean = 0
    major = minor = 0
    by_type = {}
    spend = 0.0
    changed = 0
    open_major = []
    for cid in manifest["chapters"]:
        rec = load_record(args.run, cid)
        if not rec or "review" not in rec:
            continue
        reviewed += 1
        for r in rec.get("review_history", []) + [rec["review"]]:
            spend += cost(r["usage"], r["model"], r["batch"])
        for f in rec.get("fixes", []):
            spend += cost(f["usage"], f["model"], False)
            changed += len(f["changed"])
        fs = rec["review"]["findings"]
        clean += not fs
        for f in fs:
            by_type[f["type"]] = by_type.get(f["type"], 0) + 1
            if f["severity"] == "major":
                major += 1
                open_major.append((cid, f))
            else:
                minor += 1
    print(f"Review of run {args.run}: {reviewed} chapters reviewed, {clean} with no findings")
    print(f"  open findings: {major} major, {minor} minor  {by_type}")
    print(f"  verses changed by fixes: {changed}")
    print(f"  review and fix cost so far: ${spend:.2f} (reference prices)")
    for cid, f in open_major[: args.show if hasattr(args, 'show') and args.show else 0]:
        print(f"  {cid} v{f['verse']} {f['type']}: {f['problem'][:160]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("--run", required=True)
        p.add_argument("--model", default=DEFAULT_REVIEW_MODEL)
        p.add_argument("--effort", default=DEFAULT_REVIEW_EFFORT, choices=["low", "medium", "high", "xhigh", "max"])

    p = sub.add_parser("seedtest"); common(p); p.set_defaults(fn=cmd_seedtest)
    p = sub.add_parser("submit"); common(p); p.add_argument("--only", action="append"); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_submit)
    p = sub.add_parser("collect"); p.add_argument("--run", required=True); p.set_defaults(fn=cmd_collect)
    p = sub.add_parser("fix"); p.add_argument("--run", required=True); p.add_argument("--parallel", type=int, default=8); p.set_defaults(fn=cmd_fix)
    p = sub.add_parser("report"); p.add_argument("--run", required=True); p.add_argument("--show", type=int, default=0); p.set_defaults(fn=cmd_report)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
