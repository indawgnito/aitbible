# AIT translator

Translates the Greek New Testament (SBLGNT) into English with a Claude model, one chapter per request, and checks every result against the Greek source before it can be published.

## How it fits together

| File | What it does |
|---|---|
| `source.py` | The verse inventory and lemmas from MorphGNT. The model fills this list; it cannot add, merge or drop a verse. |
| `register.json` | The decision register: Greek words with one agreed rendering each. `active` entries are sent to the model, `watch` entries are only counted by the audit. |
| `prompt_v2.py` | The system prompt (principles) and the JSON output schema. Register entries are injected per chapter for the words that occur in it. |
| `pipeline.py` | Runs, validates, patches and exports translations. |
| `audit.py` | Counts missing verses, markup, speaker errors, notes, and how each register word was rendered. |
| `build_glossary.py` | Generates the site's glossary and homepage examples from the register and a run. |
| `runs/` | One folder per run: manifest (model, prompt hash, register version), the prompt and register used, and one record per chapter with the raw response, token usage and validation result. |

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
git clone https://github.com/morphgnt/sblgnt.git greek_texts
echo "ANTHROPIC_API_KEY=..." > .env    # gitignored
```

## A full run

```bash
.venv/bin/python pipeline.py preview --book mark --chapter 1   # see the request, no API call
.venv/bin/python pipeline.py run --book philemon               # one book in real time
.venv/bin/python pipeline.py submit --nt                       # whole New Testament by batch (50% price)
.venv/bin/python pipeline.py status  --run RUN
.venv/bin/python pipeline.py collect --run RUN                 # download and validate
.venv/bin/python pipeline.py retry   --run RUN                 # redo chapters that failed validation
.venv/bin/python pipeline.py export  --run RUN                 # to runs/RUN/export
python3 audit.py --data runs/RUN/export                        # check before publishing
.venv/bin/python pipeline.py export  --run RUN --publish       # replace web/data/*.xml
python3 build_glossary.py --run RUN                            # glossary.json and examples.json
```

## Changing a rendering

The register is the only place a rendering decision lives.

1. Edit the entry in `register.json` and bump `version`.
2. `pipeline.py patch --run RUN --lemma WORD --dry-run` lists the chapters where that word is not rendered the agreed way.
3. Run it without `--dry-run` to re-translate those chapters. The old record is kept under `previous_attempts`.
4. Export, audit, rebuild the glossary.

A run never edits the register. Each chapter also returns up to five `candidates`: words the model thinks need one decision for the whole New Testament. Tally them after a run to find new entries.

Demote an entry to `watch` only on evidence. `pipeline.py run --no-register` translates chapters with the register off, which shows what the model does unaided.

## Validation

A chapter is rejected, and retried with the reasons, if the response was cut off or refused, a verse is missing, extra, duplicated or out of order, a verse is empty, or the text contains markup. Warnings (reported, not blocking) cover register words rendered another way without an explaining note, suspicious word counts, and bracket mismatches.

Not yet built: a second-pass review that checks each verse against the Greek for omitted clauses.

## Licences

SBLGNT text: CC BY 4.0. MorphGNT: CC BY-SA 3.0.
