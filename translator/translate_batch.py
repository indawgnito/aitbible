#!/usr/bin/env python3
"""
Batch translation script for the AIT Bible project.

Uses batch APIs for 50% cost savings on large translation jobs.
- Anthropic Claude: Batch Messages API
- Google Gemini: Batch API with inline requests
"""

import os
import sys
import time
import json
import re
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

import anthropic

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from greek_parser import GreekTextParser
from prompt_template import build_prompt
from utils import export_book_to_json
from xml_export import export_book_to_xml


# Configuration
DEFAULT_MODEL = "gemini-3-flash"
MAX_TOKENS = 16000
THINKING_BUDGET = 10000
POLL_INTERVAL = 30
MAX_RETRIES = 3

MODEL_MAP = {
    "opus-4-5": "claude-opus-4-5",
    "sonnet-4-5": "claude-sonnet-4-5",
    "claude-opus-4-5": "claude-opus-4-5",
    "claude-sonnet-4-5": "claude-sonnet-4-5",
    "gemini-3": "gemini-3-preview",
    "gemini-3-flash": "gemini-3-flash-preview",
    "gemini-3-preview": "gemini-3-preview",
    "gemini-3-flash-preview": "gemini-3-flash-preview",
}


def get_model_provider(model_id: str) -> str:
    if model_id.startswith("claude-"):
        return "anthropic"
    elif model_id.startswith("gemini-"):
        return "google"
    else:
        raise ValueError(f"Unknown model provider for: {model_id}")


def get_anthropic_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def get_google_client():
    if genai is None:
        print("Error: google-genai package not installed.")
        print("Install it with: pip install google-genai")
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        sys.exit(1)

    return genai.Client(api_key=api_key)


def create_batch_request_anthropic(
    book_name: str,
    chapter_num: int,
    greek_text: str,
    model: str,
    use_thinking: bool = False,
) -> dict:
    prompt = build_prompt(
        source_text=greek_text,
        book_name=book_name,
        chapter_num=chapter_num,
    )
    
    params = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    
    if use_thinking:
        params["thinking"] = {
            "type": "enabled",
            "budget_tokens": THINKING_BUDGET,
        }
    
    return {
        "custom_id": f"{book_name}-{chapter_num:02d}",
        "params": params,
    }


def submit_batch(
    client,
    parser: GreekTextParser,
    book_name: str,
    model: str,
    use_thinking: bool = False,
    chapters: Optional[list[int]] = None,
    output_dir: Path = None,
    parallel: Optional[int] = None,
) -> str:
    model_id = MODEL_MAP.get(model, model)
    provider = get_model_provider(model_id)
    chapter_count = parser.get_chapter_count(book_name)

    if chapters is None:
        chapters = list(range(1, chapter_count + 1))

    print(f"Preparing batch for {book_name.title()} ({len(chapters)} chapters)...")

    if provider == "anthropic":
        requests = []
        for chapter_num in chapters:
            greek_text = parser.get_chapter_text(book_name, chapter_num)
            req = create_batch_request_anthropic(book_name, chapter_num, greek_text, model_id, use_thinking)
            requests.append(req)

        batch = client.messages.batches.create(requests=requests)
        print(f"  Submitted Anthropic Batch ID: {batch.id}")
        return batch.id

    elif provider == "google":
        # Build list of request dicts (Inline Batch)
        requests = []
        for chapter_num in chapters:
            greek_text = parser.get_chapter_text(book_name, chapter_num)
            prompt = build_prompt(source_text=greek_text, book_name=book_name, chapter_num=chapter_num)

            req = {
                "contents": [
                    {"role": "user", "parts": [{"text": prompt}]}
                ]
            }

            if use_thinking:
                req["generation_config"] = {
                    "thinking_config": {"thinking_level": "HIGH"}
                }

            requests.append(req)

        batch_job = client.batches.create(
            model=model_id,
            src=requests,
            config={"display_name": f"{book_name}-translation"}
        )
        print(f"  Submitted Gemini Batch ID: {batch_job.name}")
        return batch_job.name


def check_batch_status(client, batch_id: str, provider: str) -> dict:
    if provider == "anthropic":
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        total = counts.succeeded + counts.errored + counts.canceled + counts.expired + counts.processing
        return {
            "id": batch.id, "status": batch.processing_status, "provider": "anthropic",
            "counts": {"total": total, "succeeded": counts.succeeded, "errored": counts.errored, "processing": counts.processing}
        }
    elif provider == "google":
        batch = client.batches.get(name=batch_id)
        state_str = str(batch.state)
        status = "ended" if "SUCCEEDED" in state_str or "FAILED" in state_str or "CANCELLED" in state_str else "in_progress"
        
        # Robustly determine total count
        total = getattr(batch, 'request_count', 0)
        if total == 0:
            if hasattr(batch, 'src') and batch.src is not None:
                try: total = len(batch.src)
                except: total = 0
            # Also check dest for completed responses
            if total == 0 and hasattr(batch, 'dest') and hasattr(batch.dest, 'inlined_responses'):
                 total = len(batch.dest.inlined_responses)

        return {
            "id": batch.name, "status": status, "state": state_str, "provider": "google",
            "counts": {
                "total": total,
                "succeeded": total if "SUCCEEDED" in state_str else 0,
                "errored": total if "FAILED" in state_str else 0,
                "processing": total if status == "in_progress" else 0
            }
        }


def download_batch_results(
    client, batch_id: str, book_name: str, output_dir: Path, provider: str, parser: Optional[GreekTextParser] = None, json_dir: Optional[Path] = None, export_xml_flag: bool = False
) -> list[Path]:
    print(f"Downloading results for {book_name.title()} (Batch {batch_id})...")
    book_dir = output_dir / book_name.lower()
    book_dir.mkdir(parents=True, exist_ok=True)
    saved_files = []

    if provider == "anthropic":
        for result in client.messages.batches.results(batch_id):
            if result.result.type == "succeeded":
                chapter_num = int(result.custom_id.split("-")[-1])
                response_text = "".join(b.text for b in result.result.message.content if b.type == "text")
                save_chapter_file(book_dir, book_name, chapter_num, response_text)
                saved_files.append(book_dir / f"chapter_{chapter_num:02d}.txt")

    elif provider == "google":
        batch = client.batches.get(name=batch_id)
        
        # 1. Check for INLINE responses (This is what you have)
        if hasattr(batch, 'dest') and hasattr(batch.dest, 'inlined_responses') and batch.dest.inlined_responses:
            print(f"  Found {len(batch.dest.inlined_responses)} inline responses.")
            for i, item in enumerate(batch.dest.inlined_responses):
                # Map index to chapter number (0 -> 1, 1 -> 2, etc.)
                # NOTE: This assumes we submitted chapters 1, 2, 3... in order.
                chapter_num = i + 1
                
                # Extract text
                # item is an InlinedResponse object containing 'response' (GenerateContentResponse)
                if hasattr(item, 'response') and item.response:
                    candidates = item.response.candidates
                    if candidates:
                        parts = candidates[0].content.parts
                        text = "".join(p.text for p in parts)
                        save_chapter_file(book_dir, book_name, chapter_num, text)
                        saved_files.append(book_dir / f"chapter_{chapter_num:02d}.txt")
                        print(f"  Saved {book_name} {chapter_num}")
                    else:
                        print(f"  Warning: No candidates for chapter {chapter_num}")
                else:
                    print(f"  Warning: Empty response for chapter {chapter_num}")

        # 2. Check for FILE responses (The old way, fallback)
        elif hasattr(batch, 'dest') and hasattr(batch.dest, 'file_name') and batch.dest.file_name:
            try:
                content = client.files.download(file=batch.dest.file_name).decode('utf-8')
                for line in content.splitlines():
                    if not line.strip(): continue
                    res = json.loads(line)
                    if res.get('status') == 'SUCCESS':
                        # Try to parse chapter from text since keys are missing
                        # ... (Simplified logic as we know you have inline responses)
                        pass 
            except Exception as e:
                print(f"  Error downloading file content: {e}")
        else:
            print(f"  No results found. State: {batch.state}")
            if hasattr(batch, 'error') and batch.error:
                 print(f"  Batch Error: {batch.error.message}")

    if parser:
        total = parser.get_chapter_count(book_name)
        if len(saved_files) >= total - 1:
            if export_xml_flag:
                export_xml(book_name, book_dir, json_dir, parser)
            else:
                export_json(book_name, book_dir, json_dir)

    return saved_files


def save_chapter_file(book_dir, book_name, chapter_num, text):
    header = f"# {book_name.title()} Chapter {chapter_num}\n# AIT Bible Translation\n# Generated by aitbible.org\n\n\n"
    (book_dir / f"chapter_{chapter_num:02d}.txt").write_text(header + text, encoding="utf-8")


def export_json(book_name, book_dir, json_dir):
    if json_dir is None: json_dir = Path(__file__).parent.parent / "web" / "data"
    try:
        export_book_to_json(book_dir, json_dir / f"{book_name.lower()}.json")
        print(f"  Exported JSON for {book_name.title()}")
    except Exception as e:
        print(f"  JSON export failed: {e}")


def export_xml(book_name, book_dir, xml_dir, parser: Optional[GreekTextParser] = None):
    if xml_dir is None: xml_dir = Path(__file__).parent.parent / "web" / "data"
    try:
        book_id = book_name.lower()
        book_display_name = book_name.title()
        export_book_to_xml(book_dir, xml_dir / f"{book_id}.xml", book_id, book_display_name, parser)
        print(f"  Exported XML for {book_name.title()}")
    except Exception as e:
        print(f"  XML export failed: {e}")


def save_batch_id(batch_id, book_name, output_dir, provider):
    (output_dir / f".batch_{book_name.lower()}.json").write_text(
        json.dumps({"batch_id": batch_id, "book": book_name, "provider": provider, "created": datetime.now().isoformat()}, indent=2)
    )


def load_batch_id(book_name, output_dir):
    f = output_dir / f".batch_{book_name.lower()}.json"
    if f.exists():
        d = json.loads(f.read_text())
        return d.get("batch_id"), d.get("provider", "anthropic")
    return None


def main():
    parser = argparse.ArgumentParser(description="Batch translate biblical Greek texts")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Common args
    def add_common(p):
        p.add_argument("--book", "-b", help="Book name")
        p.add_argument("--new-testament", "--nt", action="store_true", help="Process entire NT")
        p.add_argument("--output", "-o", default="output", help="Output dir")
        p.add_argument("--greek-texts", "-g", default="greek_texts", help="Greek texts dir")
    
    submit = subparsers.add_parser("submit")
    add_common(submit)
    submit.add_argument("--model", "-m", default=DEFAULT_MODEL)
    submit.add_argument("--thinking", "-t", action="store_true")

    status = subparsers.add_parser("status")
    add_common(status)

    download = subparsers.add_parser("download")
    add_common(download)
    download.add_argument("--json-dir", "-j", type=Path)
    download.add_argument("--xml", action="store_true", help="Export to XML format instead of JSON")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    text_parser = GreekTextParser(args.greek_texts)
    
    # Determine books to process
    books_to_process = []
    if args.new_testament:
        books_to_process = text_parser.list_books()
        
        # === CONFIRMATION PROMPT ===
        if args.command == "submit":
            total_chapters = sum(text_parser.get_chapter_count(b) for b in books_to_process)
            print("\n" + "="*60)
            print(f"  WARNING: YOU ARE ABOUT TO SUBMIT BATCH JOBS FOR THE ENTIRE NT")
            print("="*60)
            print(f"  - Books:        {len(books_to_process)}")
            print(f"  - Chapters:     {total_chapters}")
            print(f"  - Model:        {args.model}")
            print(f"  - Thinking:     {'ENABLED' if args.thinking else 'Disabled'}")
            print("\nType 'Y' to confirm and proceed, or anything else to cancel.")
            
            if input("> ").strip().upper() != 'Y':
                print("Operation cancelled.")
                sys.exit(0)
            print("Starting Bulk Submission...")

    elif args.book:
        books_to_process = [args.book]
    else:
        print("Error: Must specify --book or --new-testament")
        sys.exit(1)

    # Initialize Client
    client = None
    if args.command == "submit":
        model_id = MODEL_MAP.get(args.model, args.model)
        provider = get_model_provider(model_id)
        client = get_anthropic_client() if provider == "anthropic" else get_google_client()
    else:
        try: client = get_google_client() 
        except: pass 

    for book in books_to_process:
        if args.command == "submit":
            try:
                batch_id = submit_batch(client, text_parser, book, args.model, args.thinking, output_dir=output_dir)
                save_batch_id(batch_id, book, output_dir, provider)
                time.sleep(0.5) # Slight delay to be safe
            except Exception as e:
                print(f"Failed to submit batch for {book}: {e}")
        
        elif args.command == "status":
            saved = load_batch_id(book, output_dir)
            if saved:
                if saved[1] == "anthropic" and not isinstance(client, anthropic.Anthropic):
                    client = get_anthropic_client()
                elif saved[1] == "google" and not hasattr(client, "batches"):
                    client = get_google_client()
                
                try:
                    st = check_batch_status(client, saved[0], saved[1])
                    
                    # Fix for "0/0" display: Use local count if API reports 0
                    succeeded = st['counts']['succeeded']
                    total = st['counts']['total']
                    if total == 0:
                        total = text_parser.get_chapter_count(book)
                        
                    print(f"{book.title()}: {st['status']} ({succeeded}/{total})")
                except Exception as e:
                    print(f"{book.title()}: Error checking status - {e}")
            else:
                print(f"{book.title()}: No batch found")

        elif args.command == "download":
            saved = load_batch_id(book, output_dir)
            if saved:
                if saved[1] == "anthropic" and not isinstance(client, anthropic.Anthropic):
                    client = get_anthropic_client()
                elif saved[1] == "google" and not hasattr(client, "batches"):
                    client = get_google_client()

                try:
                    download_batch_results(
                        client, saved[0], book, output_dir, saved[1],
                        parser=text_parser, json_dir=args.json_dir,
                        export_xml_flag=args.xml
                    )
                except Exception as e:
                    print(f"Error downloading {book}: {e}")
            else:
                print(f"Skipping {book}: No active batch found.")

if __name__ == "__main__":
    main()