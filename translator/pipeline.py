#!/usr/bin/env python3
"""
AIT translation pipeline (v2).

    python pipeline.py preview --book mark --chapter 1      # show the request, no API call
    python pipeline.py run     --book mark                  # translate now, one call per chapter
    python pipeline.py submit  --nt                         # submit a batch (50% price)
    python pipeline.py status  --run RUN
    python pipeline.py collect --run RUN                    # download + validate batch results
    python pipeline.py retry   --run RUN                    # re-run chapters that failed validation
    python pipeline.py patch   --run RUN --lemma WORD       # after a register change: redo affected chapters
    python pipeline.py usage   --run RUN                    # tokens and cost
    python pipeline.py export  --run RUN                    # write runs/RUN/export/<book>.xml
    python pipeline.py export  --run RUN --publish          # replace web/data/<book>.xml

Every run lives in translator/runs/<RUN>/ with a manifest (model, effort,
prompt hash, register hash) and one JSON record per chapter holding the raw
response, token usage, the parsed translation and its validation result.
Nothing is exported unless it validates against the Greek source.
"""

import argparse
import datetime
import hashlib
import html
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from prompt_v2 import (OUTPUT_SCHEMA, SYSTEM_PROMPT, applicable_entries,
                       build_user_message, prompt_hash)
from source import BOOKS, Source, SourceVerse

ROOT = Path(__file__).resolve().parent
RUNS_DIR = ROOT / "runs"
REGISTER_PATH = ROOT / "register.json"
WEB_DATA = ROOT.parent / "web" / "data"

DEFAULT_MODEL = "claude-fable-5-2"
DEFAULT_EFFORT = "high"
# Thinking is billed as output and counts toward this cap, so it is set well
# above the largest chapter's visible output.
MAX_TOKENS = 48000
MAX_ATTEMPTS = 3

# USD per million tokens (input, output). Reference table dated 2026-11-03;
# check the live pricing page before relying on the dollar figures.
PRICES = {
    "claude-fable-5-2": (8.00, 40.00),
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}

BOOK_TITLES = {
    "matthew": "Matthew", "mark": "Mark", "luke": "Luke", "john": "John", "acts": "Acts",
    "romans": "Romans", "1corinthians": "1 Corinthians", "2corinthians": "2 Corinthians",
    "galatians": "Galatians", "ephesians": "Ephesians", "philippians": "Philippians",
    "colossians": "Colossians", "1thessalonians": "1 Thessalonians",
    "2thessalonians": "2 Thessalonians", "1timothy": "1 Timothy", "2timothy": "2 Timothy",
    "titus": "Titus", "philemon": "Philemon", "hebrews": "Hebrews", "james": "James",
    "1peter": "1 Peter", "2peter": "2 Peter", "1john": "1 John", "2john": "2 John",
    "3john": "3 John", "jude": "Jude", "revelation": "Revelation",
}


# ---------------------------------------------------------------- setup

def load_env():
    """Read translator/.env (KEY=value lines) without overriding the environment."""
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_client():
    import anthropic
    load_env()
    return anthropic.Anthropic()


def load_register() -> dict:
    return json.loads(REGISTER_PATH.read_text(encoding="utf-8"))


def register_hash() -> str:
    return hashlib.sha256(REGISTER_PATH.read_bytes()).hexdigest()[:12]


def custom_id(book: str, chapter: int) -> str:
    return f"{book}-{chapter:03d}"


def parse_custom_id(cid: str) -> Tuple[str, int]:
    book, ch = cid.rsplit("-", 1)
    return book, int(ch)


# ---------------------------------------------------------------- requests

def preceding_context(src: Source, book: str, chapter: int) -> List[SourceVerse]:
    chapters = src.chapters(book)
    if chapter == chapters[0]:
        return []
    return src.chapter(book, chapter - 1)[-3:]


def build_params(src: Source, register: dict, book: str, chapter: int,
                 model: str, effort: str, feedback: Optional[str] = None) -> dict:
    verses = src.chapter(book, chapter)
    user = build_user_message(BOOK_TITLES[book], chapter, verses, register,
                              preceding_context(src, book, chapter))
    if feedback:
        user += ("\n\nA previous attempt at this chapter was rejected by the validator for "
                 f"these reasons. Correct them in this attempt:\n{feedback}")
    return {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": user}],
        "output_config": {
            "effort": effort,
            "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
        },
    }


# ---------------------------------------------------------------- validation

_MARKUP = re.compile(r"\*\*|(?<![\w*])\*\w|\[/?[A-Z]{3,}|^#|</?\w+>")
_LEADING_NUM = re.compile(r"^\d+[\s.:]")


def segments_text(segments: List[dict]) -> str:
    return " ".join(s["text"].strip() for s in segments if s["text"].strip())


def _stem_pattern(rendering: str) -> Optional[re.Pattern]:
    """Loose match for a rendering: tolerates inflection and a few words in between."""
    words = re.findall(r"[A-Za-z'-]+", rendering)
    if not words:
        return None
    parts = []
    for w in words:
        if len(w) > 3 and w.endswith("y"):
            parts.append(re.escape(w[:-1]) + r"(?:y|ies|ied)\w*")
        elif len(w) > 3 and w.endswith("s"):
            parts.append(re.escape(w[:-1]) + r"\w*")
        else:
            parts.append(re.escape(w) + r"\w*")
    return re.compile(r"\b" + r"\W+(?:[\w'’-]+\W+){0,3}?".join(parts), re.IGNORECASE)


def _patterns(forms: List[str]) -> List[re.Pattern]:
    pats = []
    for f in forms:
        for piece in f.split(" / "):
            p = _stem_pattern(piece)
            if p:
                pats.append(p)
    return pats


def entry_forms(entry: dict) -> Dict[str, List[str]]:
    """Accepted renderings per lemma: the entry's own lemma and each family lemma."""
    alts = [a["rendering"] for a in entry.get("alternates", [])]
    forms = {entry["lemma"]: [entry["default"]] + alts}
    for lem, rendering in entry.get("family", {}).items():
        forms[lem] = [rendering]
    return forms


def validate(parsed: dict, verses: List[SourceVerse], register: dict) -> Tuple[List[str], List[str]]:
    """Return (errors, warnings). Errors block export; warnings are reported."""
    errors, warnings = [], []
    want = [v.verse for v in verses]
    got = [v["verse"] for v in parsed.get("verses", [])]
    if got != want:
        missing = [n for n in want if n not in got]
        extra = [n for n in got if n not in want]
        dupes = sorted({n for n in got if got.count(n) > 1})
        detail = []
        if missing:
            detail.append(f"missing verses {missing}")
        if extra:
            detail.append(f"verses not in the source {extra}")
        if dupes:
            detail.append(f"duplicated verses {dupes}")
        if not detail:
            detail.append("verses out of order")
        errors.append("Verse list does not match the source: " + "; ".join(detail) + ".")

    texts: Dict[int, str] = {}
    by_num = {v.verse: v for v in verses}
    for v in parsed.get("verses", []):
        n = v["verse"]
        text = segments_text(v["segments"])
        texts[n] = text
        if not text:
            errors.append(f"Verse {n} is empty.")
            continue
        if _MARKUP.search(text):
            errors.append(f"Verse {n} contains markup or tags: {text[:80]!r}")
        if _LEADING_NUM.match(text):
            errors.append(f"Verse {n} begins with a number, which suggests a merged verse: {text[:60]!r}")
        if re.search(rf"(?<=[a-z,;.”] ){n + 1} [A-Za-z“]", text):
            warnings.append(f"Verse {n} contains the number {n + 1} mid-text; check for a merged verse.")
        src_v = by_num.get(n)
        if src_v is not None:
            ratio = len(text.split()) / max(1, len(src_v.words))
            if len(src_v.words) >= 6 and (ratio < 0.5 or ratio > 3.5):
                warnings.append(f"Verse {n}: {len(text.split())} English words for "
                                f"{len(src_v.words)} Greek; check for omission or expansion.")
            for b_open, b_close in (("⟦", "⟧"), ("[", "]")):
                if (b_open in src_v.greek) != (b_open in text) or (b_close in src_v.greek) != (b_close in text):
                    warnings.append(f"Verse {n}: bracket {b_open}{b_close} does not match the source.")

    exception_notes = set()
    for note in parsed.get("notes", []):
        n = note["verse"]
        if n not in by_num:
            errors.append(f"A note refers to verse {n}, which is not in this chapter.")
            continue
        if not note["note"].strip() or not note["phrase"].strip():
            errors.append(f"A note on verse {n} is missing its phrase or text.")
        phrase = note["phrase"].strip().strip("“”\"'‘’")
        if phrase and phrase.lower() not in texts.get(n, "").lower():
            warnings.append(f"Note on verse {n}: phrase {phrase!r} does not appear in the verse.")
        if note["kind"] == "register-exception":
            exception_notes.add((n, note["lemma"]))

    entries, occurrences = applicable_entries(register, verses)
    for e in entries:
        for lem, forms in entry_forms(e).items():
            pats = _patterns(forms)
            for n in occurrences.get(lem, []):
                text = texts.get(n, "")
                if text and not any(p.search(text) for p in pats) and (n, lem) not in exception_notes:
                    warnings.append(f"Verse {n}: {lem} is not rendered with a register form "
                                    f"({'; '.join(forms)}) and has no register-exception note.")
    return errors, warnings


# ---------------------------------------------------------------- records

def run_dir(run: str) -> Path:
    return RUNS_DIR / run


def new_run(model: str, effort: str, mode: str, chapters: List[Tuple[str, int]], label: str = "",
            register: Optional[dict] = None) -> str:
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run = f"{stamp}-{label}" if label else stamp
    d = run_dir(run)
    (d / "chapters").mkdir(parents=True)
    manifest = {
        "run": run, "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "mode": mode, "model": model, "effort": effort, "max_tokens": MAX_TOKENS,
        "prompt_hash": prompt_hash(),
        "register_hash": register_hash() if register is None else "none",
        "register_version": (register or load_register())["version"],
        "chapters": [custom_id(b, c) for b, c in chapters],
    }
    (d / "manifest.json").write_text(json.dumps(manifest, indent=2))
    (d / "system_prompt.txt").write_text(SYSTEM_PROMPT, encoding="utf-8")
    (d / "register.json").write_text(
        REGISTER_PATH.read_text(encoding="utf-8") if register is None
        else json.dumps(register, ensure_ascii=False, indent=2), encoding="utf-8")
    return run


def load_manifest(run: str) -> dict:
    return json.loads((run_dir(run) / "manifest.json").read_text())


def save_manifest(run: str, manifest: dict):
    (run_dir(run) / "manifest.json").write_text(json.dumps(manifest, indent=2))


def record_path(run: str, cid: str) -> Path:
    return run_dir(run) / "chapters" / f"{cid}.json"


def load_record(run: str, cid: str) -> Optional[dict]:
    p = record_path(run, cid)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def make_record(src: Source, register: dict, cid: str, message, batch: bool, attempt: int) -> dict:
    """Turn an API message into a stored, validated chapter record."""
    book, chapter = parse_custom_id(cid)
    raw = "".join(b.text for b in message.content if b.type == "text")
    usage = message.usage
    rec = {
        "id": cid, "book": book, "chapter": chapter, "model": message.model,
        "message_id": message.id, "stop_reason": message.stop_reason,
        "batch": batch, "attempt": attempt,
        "usage": {"input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens},
        "raw": raw, "parsed": None, "errors": [], "warnings": [],
    }
    if message.stop_reason != "end_turn":
        rec["errors"].append(f"Response did not finish normally (stop_reason={message.stop_reason}).")
        return rec
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        rec["errors"].append(f"Response is not valid JSON: {e}")
        return rec
    rec["parsed"] = parsed
    rec["errors"], rec["warnings"] = validate(parsed, src.chapter(book, chapter), register)
    return rec


def save_record(run: str, rec: dict):
    p = record_path(run, rec["id"])
    # Keep every attempt's raw response; the newest attempt is the record.
    if p.exists():
        old = json.loads(p.read_text(encoding="utf-8"))
        rec["previous_attempts"] = old.get("previous_attempts", []) + [
            {k: old[k] for k in ("attempt", "message_id", "stop_reason", "usage", "raw", "errors")}]
    p.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------------------------------------------------------- commands

def select_chapters(src: Source, args) -> List[Tuple[str, int]]:
    if getattr(args, "nt", False):
        return src.all_chapters()
    if getattr(args, "only", None):
        return [(o.split(":")[0].lower(), int(o.split(":")[1])) for o in args.only]
    if not args.book:
        sys.exit("Specify --book (repeatable) or --nt.")
    out = []
    for book in args.book:
        book = book.lower()
        if book not in BOOKS:
            sys.exit(f"Unknown book: {book}")
        chapters = src.chapters(book)
        if getattr(args, "chapter", None):
            chapters = [c for c in chapters if c in args.chapter]
        out += [(book, c) for c in chapters]
    return out


def translate_one(client, src, register, run, book, chapter, model, effort, first_attempt=1,
                  feedback: Optional[str] = None, patch: Optional[dict] = None) -> dict:
    """Real-time translation of one chapter, retried with validator feedback."""
    cid = custom_id(book, chapter)
    rec = None
    for attempt in range(first_attempt, first_attempt + MAX_ATTEMPTS):
        params = build_params(src, register, book, chapter, model, effort, feedback)
        with client.messages.stream(**params) as stream:
            message = stream.get_final_message()
        rec = make_record(src, register, cid, message, batch=False, attempt=attempt)
        if patch:
            rec["patch"] = patch
        save_record(run, rec)
        if not rec["errors"]:
            break
        if rec["stop_reason"] == "refusal":
            break
        feedback = "\n".join(f"- {e}" for e in rec["errors"])
    return rec


def cmd_preview(args):
    src, register = Source(), load_register()
    for book, chapter in select_chapters(src, args):
        p = build_params(src, register, book, chapter, args.model, args.effort)
        print(f"=== {custom_id(book, chapter)}  model={p['model']}  effort={args.effort}")
        if args.system:
            print(p["system"], "\n")
        print(p["messages"][0]["content"])
        print(f"\n[system {len(p['system'])} chars, user {len(p['messages'][0]['content'])} chars]\n")


def cmd_run(args):
    src, register = Source(), load_register()
    chapters = select_chapters(src, args)
    client = get_client()
    off = None
    if args.no_register:  # experiment: does the model stay consistent on its own?
        off = register = {"version": "none", "entries": []}
    run = args.run or new_run(args.model, args.effort, "realtime", chapters, args.label, off)
    print(f"Run {run}: {len(chapters)} chapters on {args.model}, effort {args.effort}")

    def work(bc):
        rec = translate_one(client, src, register, run, bc[0], bc[1], args.model, args.effort)
        flag = "ok" if not rec["errors"] else "FAILED"
        print(f"  {rec['id']}: {flag}, attempt {rec['attempt']}, "
              f"{rec['usage']['output_tokens']} output tokens, {len(rec['warnings'])} warnings")
        return rec

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        list(pool.map(work, chapters))
    cmd_usage(argparse.Namespace(run=run))


def cmd_submit(args):
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    src, register = Source(), load_register()
    chapters = select_chapters(src, args)
    client = get_client()
    requests = [Request(custom_id=custom_id(b, c),
                        params=MessageCreateParamsNonStreaming(
                            **build_params(src, register, b, c, args.model, args.effort)))
                for b, c in chapters]
    if not args.yes:
        print(f"About to submit {len(requests)} chapters to the Batch API on {args.model} "
              f"(effort {args.effort}). This spends API credit.")
        if input("Type 'yes' to submit: ").strip().lower() != "yes":
            sys.exit("Cancelled.")
    run = new_run(args.model, args.effort, "batch", chapters, args.label)
    batch = client.messages.batches.create(requests=requests)
    manifest = load_manifest(run)
    manifest["batch_id"] = batch.id
    save_manifest(run, manifest)
    print(f"Run {run}: submitted batch {batch.id} ({len(requests)} chapters).")


def cmd_status(args):
    manifest = load_manifest(args.run)
    client = get_client()
    b = client.messages.batches.retrieve(manifest["batch_id"])
    c = b.request_counts
    print(f"{b.id}: {b.processing_status} — succeeded {c.succeeded}, processing {c.processing}, "
          f"errored {c.errored}, expired {c.expired}, canceled {c.canceled}")


def cmd_collect(args):
    manifest = load_manifest(args.run)
    src = Source()
    register = json.loads((run_dir(args.run) / "register.json").read_text(encoding="utf-8"))
    client = get_client()
    b = client.messages.batches.retrieve(manifest["batch_id"])
    if b.processing_status != "ended":
        sys.exit(f"Batch is still {b.processing_status}; nothing collected.")
    seen, failed = set(), []
    for result in client.messages.batches.results(manifest["batch_id"]):
        cid = result.custom_id
        seen.add(cid)
        if result.result.type != "succeeded":
            failed.append(cid)
            detail = getattr(getattr(result.result, "error", None), "type", "")
            book, chapter = parse_custom_id(cid)
            save_record(args.run, {
                "id": cid, "book": book, "chapter": chapter, "model": manifest["model"],
                "message_id": None, "stop_reason": None, "batch": True, "attempt": 1,
                "usage": {"input_tokens": 0, "output_tokens": 0}, "raw": "", "parsed": None,
                "errors": [f"Batch request {result.result.type} {detail}".strip()], "warnings": []})
            continue
        existing = load_record(args.run, cid)
        if existing and existing.get("message_id") == result.result.message.id:
            continue
        if existing and not existing["errors"]:
            continue  # already repaired by `retry`; keep the valid record
        rec = make_record(src, register, cid, result.result.message, batch=True, attempt=1)
        save_record(args.run, rec)
        if rec["errors"]:
            failed.append(cid)
    never = [c for c in manifest["chapters"] if c not in seen]
    print(f"Collected {len(seen)} results; {len(failed)} failed validation; {len(never)} missing from the batch.")
    for cid in failed + never:
        rec = load_record(args.run, cid)
        print(f"  {cid}: {rec['errors'][0] if rec else 'no result returned'}")
    cmd_usage(args)


def cmd_retry(args):
    manifest = load_manifest(args.run)
    src = Source()
    register = json.loads((run_dir(args.run) / "register.json").read_text(encoding="utf-8"))
    todo = []
    for cid in manifest["chapters"]:
        rec = load_record(args.run, cid)
        if rec is None or rec["errors"]:
            todo.append((cid, rec))
    if not todo:
        print("Nothing to retry: every chapter validates.")
        return
    print(f"Retrying {len(todo)} chapters in real time on {manifest['model']} (full price).")
    client = get_client()

    def work(item):
        cid, rec = item
        book, chapter = parse_custom_id(cid)
        feedback = "\n".join(f"- {e}" for e in rec["errors"]) if rec and rec.get("parsed") else None
        new = translate_one(client, src, register, args.run, book, chapter, manifest["model"],
                            manifest["effort"], first_attempt=(rec["attempt"] + 1 if rec else 1),
                            feedback=feedback)
        print(f"  {cid}: {'ok' if not new['errors'] else 'STILL FAILING: ' + new['errors'][0]}")

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        list(pool.map(work, todo))
    cmd_usage(args)


def cmd_patch(args):
    """Re-translate chapters of a finished run under the current register.

    Use after a register change: pass --lemma to pick every chapter where that
    Greek word is not rendered with a register form, or --only for chapters by
    hand. The old record is kept under previous_attempts.
    """
    manifest = load_manifest(args.run)
    src, register = Source(), load_register()
    todo = [(o.split(":")[0].lower(), int(o.split(":")[1])) for o in (args.only or [])]
    if args.lemma:
        entry = next((e for e in register["entries"]
                      if args.lemma in [e["lemma"]] + list(e.get("family", {}))), None)
        if entry is None:
            sys.exit(f"No register entry covers {args.lemma}.")
        pats = _patterns(entry_forms(entry)[args.lemma])
        for cid in manifest["chapters"]:
            rec = load_record(args.run, cid)
            book, chapter = parse_custom_id(cid)
            texts = {v["verse"]: segments_text(v["segments"]) for v in rec["parsed"]["verses"]}
            if any(args.lemma in sv.lemmas and not any(p.search(texts[sv.verse]) for p in pats)
                   for sv in src.chapter(book, chapter)) and (book, chapter) not in todo:
                todo.append((book, chapter))
    if not todo:
        print("Nothing to patch.")
        return
    print(f"Patching {len(todo)} chapters under register {register['version']} "
          f"on {manifest['model']} (real time, full price): "
          + ", ".join(f"{b} {c}" for b, c in todo))
    if args.dry_run:
        return
    client = get_client()
    patch = {"register_version": register["version"], "register_hash": register_hash(),
             "reason": args.reason, "date": datetime.datetime.now().isoformat(timespec="seconds")}

    def work(bc):
        old = load_record(args.run, custom_id(*bc))
        new = translate_one(client, src, register, args.run, bc[0], bc[1], manifest["model"],
                            manifest["effort"], first_attempt=old["attempt"] + 1, patch=patch)
        print(f"  {new['id']}: {'ok' if not new['errors'] else 'FAILED: ' + new['errors'][0]}, "
              f"{len(new['warnings'])} warnings")

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        list(pool.map(work, todo))
    manifest.setdefault("patches", []).append({**patch, "chapters": [custom_id(b, c) for b, c in todo]})
    # The run's register snapshot follows the newest patch; the previous one is kept.
    snap = run_dir(args.run) / "register.json"
    snap.rename(run_dir(args.run) / f"register.{manifest['register_version']}.json")
    snap.write_text(REGISTER_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    manifest["register_version"] = register["version"]
    save_manifest(args.run, manifest)
    cmd_usage(args)


def _all_usage(rec: dict, run_is_batch: bool):
    """(usage, billed_at_batch_price) for the current record and every earlier attempt."""
    yield rec["usage"], rec["batch"]
    for prev in rec.get("previous_attempts", []):
        yield prev["usage"], run_is_batch and prev["attempt"] == 1


def cmd_usage(args):
    manifest = load_manifest(args.run)
    tin = tout = 0
    cost = 0.0
    done = ok = warn = 0
    price = PRICES.get(manifest["model"])
    for cid in manifest["chapters"]:
        rec = load_record(args.run, cid)
        if not rec:
            continue
        done += 1
        ok += not rec["errors"]
        warn += len(rec["warnings"])
        for u, batch in _all_usage(rec, manifest["mode"] == "batch"):
            tin += u["input_tokens"]
            tout += u["output_tokens"]
            if price:
                cost += (u["input_tokens"] * price[0] + u["output_tokens"] * price[1]) / 1e6 * (0.5 if batch else 1)
    total = len(manifest["chapters"])
    print(f"Run {args.run} ({manifest['model']}, {manifest['mode']}): {done}/{total} chapters returned, "
          f"{ok} valid, {warn} warnings")
    print(f"  tokens: {tin:,} in, {tout:,} out (output includes thinking)")
    if price and done:
        print(f"  estimated cost: ${cost:.2f} (${cost / done:.3f} per chapter; "
              f"reference prices, not an invoice)")
        src = Source()
        words = lambda cid: sum(len(v.words) for v in src.chapter(*parse_custom_id(cid)))
        done_words = sum(words(c) for c in manifest["chapters"] if load_record(args.run, c))
        nt_words = sum(len(v.words) for v in src.all_verses())
        if done_words < nt_words:
            scale = nt_words / done_words
            batch_factor = 0.5 if manifest["mode"] == "realtime" else 1
            print(f"  projected for the whole New Testament, scaled by Greek word count "
                  f"({done_words:,} of {nt_words:,}): about ${cost * scale * batch_factor:.0f} by batch")


def _x(s: str) -> str:
    return html.escape(s, quote=True)


def export_book(run: str, book: str, src: Source, out_dir: Path) -> bool:
    manifest = load_manifest(run)
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<ait version="2.0" run="{_x(run)}" model="{_x(manifest["model"])}" '
             f'register="{_x(manifest["register_version"])}">',
             f'  <book id="{book}" name="{_x(BOOK_TITLES[book])}">']
    for chapter in src.chapters(book):
        rec = load_record(run, custom_id(book, chapter))
        if rec is None or rec["errors"]:
            print(f"  {book}: chapter {chapter} is missing or invalid; book not exported.")
            return False
        notes: Dict[int, List[dict]] = {}
        for n in rec["parsed"]["notes"]:
            notes.setdefault(n["verse"], []).append(n)
        src_verses = {v.verse: v for v in src.chapter(book, chapter)}
        lines.append(f'    <chapter num="{chapter}">')
        for v in rec["parsed"]["verses"]:
            sv = src_verses[v["verse"]]
            status = f' status="{sv.bracket}"' if sv.bracket else ""
            lines.append(f'      <verse num="{v["verse"]}"{status}>')
            parts = []
            for s in v["segments"]:
                text = _x(s["text"].strip())
                if not text:
                    continue
                if parts:
                    text = " " + text
                if s["speaker"] == "narrator":
                    parts.append(text)
                else:
                    parts.append(f'<q who="{s["speaker"]}">{text}</q>')
            para = "<p/>" if v["paragraph_start"] else ""
            lines.append(f'        <text>{para}{"".join(parts)}</text>')
            lines.append("        <greek>")
            for w in sv.words:
                lines.append(f'          <w lemma="{_x(w.lemma)}">{_x(w.text)}</w>')
            lines.append("        </greek>")
            for n in notes.get(v["verse"], []):
                lines.append(f'        <note term="{_x(n["phrase"])}" kind="{n["kind"]}" '
                             f'lemma="{_x(n["lemma"])}" traditional="{_x(n["traditional"])}">'
                             f'{_x(n["note"])}</note>')
            lines.append("      </verse>")
        lines.append("    </chapter>")
    lines += ["  </book>", "</ait>"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{book}.xml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return True


def cmd_export(args):
    manifest = load_manifest(args.run)
    src = Source()
    books = sorted({parse_custom_id(c)[0] for c in manifest["chapters"]}, key=BOOKS.index)
    out_dir = WEB_DATA if args.publish else (args.out or run_dir(args.run) / "export")
    done = [b for b in books if export_book(args.run, b, src, out_dir)]
    print(f"Exported {len(done)}/{len(books)} books to {out_dir}: {', '.join(done)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)

    def scope(p):
        p.add_argument("--book", "-b", action="append")
        p.add_argument("--chapter", "-c", type=int, action="append")
        p.add_argument("--nt", action="store_true", help="the whole New Testament")
        p.add_argument("--only", action="append", help="book:chapter, repeatable (overrides --book)")
        p.add_argument("--model", "-m", default=DEFAULT_MODEL)
        p.add_argument("--effort", default=DEFAULT_EFFORT, choices=["low", "medium", "high", "xhigh", "max"])
        p.add_argument("--label", default="", help="short name appended to the run id")

    p = sub.add_parser("preview"); scope(p); p.add_argument("--system", action="store_true"); p.set_defaults(fn=cmd_preview)
    p = sub.add_parser("run"); scope(p); p.add_argument("--run"); p.add_argument("--parallel", type=int, default=4); p.add_argument("--no-register", action="store_true"); p.set_defaults(fn=cmd_run)
    p = sub.add_parser("submit"); scope(p); p.add_argument("--yes", action="store_true"); p.set_defaults(fn=cmd_submit)
    for name, fn in (("status", cmd_status), ("collect", cmd_collect), ("usage", cmd_usage)):
        p = sub.add_parser(name); p.add_argument("--run", required=True); p.set_defaults(fn=fn)
    p = sub.add_parser("retry"); p.add_argument("--run", required=True); p.add_argument("--parallel", type=int, default=4); p.set_defaults(fn=cmd_retry)
    p = sub.add_parser("patch"); p.add_argument("--run", required=True); p.add_argument("--lemma"); p.add_argument("--only", action="append"); p.add_argument("--reason", default=""); p.add_argument("--dry-run", action="store_true"); p.add_argument("--parallel", type=int, default=8); p.set_defaults(fn=cmd_patch)
    p = sub.add_parser("export"); p.add_argument("--run", required=True); p.add_argument("--out", type=Path); p.add_argument("--publish", action="store_true", help="write into web/data (replaces the served books)"); p.set_defaults(fn=cmd_export)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
