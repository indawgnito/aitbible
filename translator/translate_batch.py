#!/usr/bin/env python3
"""
Batch translation script for the AIT Bible project.

Uses Anthropic's Batch API for 50% cost savings on large translation jobs.
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime

import anthropic

from greek_parser import GreekTextParser
from prompt_template import build_prompt


# Configuration
DEFAULT_MODEL = "claude-sonnet-4-5"
MAX_TOKENS = 16000  # Must be > THINKING_BUDGET when thinking is enabled
THINKING_BUDGET = 10000
POLL_INTERVAL = 30  # seconds between status checks


def get_client() -> anthropic.Anthropic:
    """Initialize the Anthropic client."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)
    
    return anthropic.Anthropic(api_key=api_key)


def create_batch_request(
    book_name: str,
    chapter_num: int,
    greek_text: str,
    model: str,
    use_thinking: bool = False,
) -> dict:
    """Create a single batch request for a chapter."""
    prompt = build_prompt(
        source_text=greek_text,
        book_name=book_name,
        chapter_num=chapter_num,
    )
    
    params = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "user", "content": prompt}
        ],
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
    client: anthropic.Anthropic,
    parser: GreekTextParser,
    book_name: str,
    model: str,
    use_thinking: bool = False,
    chapters: Optional[list[int]] = None,
) -> str:
    """
    Submit a batch job for translating a book.
    
    Returns the batch ID.
    """
    chapter_count = parser.get_chapter_count(book_name)
    
    if chapters is None:
        chapters = list(range(1, chapter_count + 1))
    
    print(f"Preparing batch for {book_name.title()}")
    print(f"  Chapters: {len(chapters)}")
    print(f"  Model: {model}")
    if use_thinking:
        print(f"  Extended thinking: enabled")
    print()
    
    # Build batch requests
    requests = []
    for chapter_num in chapters:
        greek_text = parser.get_chapter_text(book_name, chapter_num)
        request = create_batch_request(
            book_name=book_name,
            chapter_num=chapter_num,
            greek_text=greek_text,
            model=model,
            use_thinking=use_thinking,
        )
        requests.append(request)
        print(f"  Prepared chapter {chapter_num}")
    
    print(f"\nSubmitting batch with {len(requests)} requests...")
    
    batch = client.messages.batches.create(requests=requests)
    
    print(f"  Batch ID: {batch.id}")
    print(f"  Status: {batch.processing_status}")
    
    return batch.id


def check_batch_status(client: anthropic.Anthropic, batch_id: str) -> dict:
    """Check the status of a batch job."""
    batch = client.messages.batches.retrieve(batch_id)
    
    counts = batch.request_counts
    total = counts.succeeded + counts.errored + counts.canceled + counts.expired + counts.processing
    
    return {
        "id": batch.id,
        "status": batch.processing_status,
        "created": batch.created_at,
        "counts": {
            "total": total,
            "succeeded": counts.succeeded,
            "errored": counts.errored,
            "processing": counts.processing,
            "canceled": counts.canceled,
            "expired": counts.expired,
        }
    }


def wait_for_batch(
    client: anthropic.Anthropic,
    batch_id: str,
    poll_interval: int = POLL_INTERVAL,
) -> bool:
    """
    Wait for a batch to complete.
    
    Returns True if successful, False if there were errors.
    """
    print(f"Waiting for batch {batch_id} to complete...")
    print(f"  (checking every {poll_interval} seconds)\n")
    
    while True:
        status = check_batch_status(client, batch_id)
        counts = status["counts"]
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"  [{timestamp}] {status['status']}: "
              f"{counts['succeeded']}/{counts['total']} complete, "
              f"{counts['processing']} processing, "
              f"{counts['errored']} errored")
        
        if status["status"] == "ended":
            print(f"\nBatch completed!")
            return counts["errored"] == 0
        
        time.sleep(poll_interval)


def download_batch_results(
    client: anthropic.Anthropic,
    batch_id: str,
    book_name: str,
    output_dir: Path,
) -> list[Path]:
    """
    Download and save batch results.
    
    Returns list of saved file paths.
    """
    print(f"\nDownloading results for batch {batch_id}...")
    
    book_dir = output_dir / book_name.lower()
    book_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    
    for result in client.messages.batches.results(batch_id):
        custom_id = result.custom_id  # e.g., "matthew-06"
        
        # Parse chapter number from custom_id
        chapter_num = int(custom_id.split("-")[-1])
        
        if result.result.type == "succeeded":
            # Extract text from response (skip thinking blocks)
            response_text = ""
            for block in result.result.message.content:
                if hasattr(block, "text") and block.type == "text":
                    response_text += block.text
            
            # Build file with header
            header_lines = [
                f"# {book_name.title()} Chapter {chapter_num}",
                f"# AIT Bible Translation",
                f"# Generated by aitbible.org",
                "",
                "",
            ]
            content = "\n".join(header_lines) + response_text
            
            # Save file
            filepath = book_dir / f"chapter_{chapter_num:02d}.txt"
            filepath.write_text(content, encoding="utf-8")
            saved_files.append(filepath)
            
            print(f"  Saved chapter {chapter_num}")
        else:
            print(f"  FAILED: chapter {chapter_num} - {result.result.type}")
    
    return saved_files


def save_batch_id(batch_id: str, book_name: str, output_dir: Path) -> Path:
    """Save batch ID to a file for later retrieval."""
    batch_file = output_dir / f".batch_{book_name.lower()}.json"
    
    data = {
        "batch_id": batch_id,
        "book": book_name,
        "created": datetime.now().isoformat(),
    }
    
    batch_file.write_text(json.dumps(data, indent=2))
    return batch_file


def load_batch_id(book_name: str, output_dir: Path) -> Optional[str]:
    """Load a previously saved batch ID."""
    batch_file = output_dir / f".batch_{book_name.lower()}.json"
    
    if not batch_file.exists():
        return None
    
    data = json.loads(batch_file.read_text())
    return data.get("batch_id")


def main():
    arg_parser = argparse.ArgumentParser(
        description="Batch translate biblical Greek texts (50% cost savings)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Submit a batch job
  %(prog)s submit --book matthew
  
  # Submit with Opus and extended thinking  
  %(prog)s submit --book matthew --model claude-opus-4-5 --thinking
  
  # Check status of a batch
  %(prog)s status --batch-id batch_abc123
  %(prog)s status --book matthew  # uses saved batch ID
  
  # Wait for completion and download results
  %(prog)s wait --book matthew
  
  # Download results from a completed batch
  %(prog)s download --book matthew
  %(prog)s download --batch-id batch_abc123 --book matthew
        """,
    )
    
    subparsers = arg_parser.add_subparsers(dest="command", help="Commands")
    
    # Submit command
    submit_parser = subparsers.add_parser("submit", help="Submit a batch job")
    submit_parser.add_argument("--book", "-b", required=True, help="Book name")
    submit_parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help="Model to use")
    submit_parser.add_argument("--thinking", "-t", action="store_true", help="Enable extended thinking")
    submit_parser.add_argument("--output", "-o", default="output", help="Output directory")
    submit_parser.add_argument("--greek-texts", "-g", default="greek_texts", help="Greek texts directory")
    submit_parser.add_argument("--chapters", help="Specific chapters (e.g., '1-10' or '1,5,7')")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check batch status")
    status_parser.add_argument("--batch-id", help="Batch ID")
    status_parser.add_argument("--book", "-b", help="Book name (to load saved batch ID)")
    status_parser.add_argument("--output", "-o", default="output", help="Output directory")
    
    # Wait command
    wait_parser = subparsers.add_parser("wait", help="Wait for batch to complete")
    wait_parser.add_argument("--batch-id", help="Batch ID")
    wait_parser.add_argument("--book", "-b", help="Book name (to load saved batch ID)")
    wait_parser.add_argument("--output", "-o", default="output", help="Output directory")
    wait_parser.add_argument("--poll-interval", type=int, default=POLL_INTERVAL, help="Seconds between checks")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download batch results")
    download_parser.add_argument("--batch-id", help="Batch ID")
    download_parser.add_argument("--book", "-b", required=True, help="Book name")
    download_parser.add_argument("--output", "-o", default="output", help="Output directory")
    
    # Run command (submit + wait + download)
    run_parser = subparsers.add_parser("run", help="Submit, wait, and download (full pipeline)")
    run_parser.add_argument("--book", "-b", required=True, help="Book name")
    run_parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help="Model to use")
    run_parser.add_argument("--thinking", "-t", action="store_true", help="Enable extended thinking")
    run_parser.add_argument("--output", "-o", default="output", help="Output directory")
    run_parser.add_argument("--greek-texts", "-g", default="greek_texts", help="Greek texts directory")
    run_parser.add_argument("--poll-interval", type=int, default=POLL_INTERVAL, help="Seconds between checks")
    
    args = arg_parser.parse_args()
    
    if not args.command:
        arg_parser.print_help()
        return
    
    client = get_client()
    output_dir = Path(args.output) if hasattr(args, 'output') else Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Helper to get batch ID from args or saved file
    def get_batch_id():
        if hasattr(args, 'batch_id') and args.batch_id:
            return args.batch_id
        if hasattr(args, 'book') and args.book:
            saved_id = load_batch_id(args.book, output_dir)
            if saved_id:
                print(f"Using saved batch ID for {args.book}: {saved_id}")
                return saved_id
        print("Error: No batch ID provided. Use --batch-id or --book with a saved batch.")
        sys.exit(1)
    
    if args.command == "submit":
        parser = GreekTextParser(args.greek_texts)
        
        # Parse chapters argument if provided
        chapters = None
        if args.chapters:
            if "-" in args.chapters:
                start, end = map(int, args.chapters.split("-"))
                chapters = list(range(start, end + 1))
            elif "," in args.chapters:
                chapters = [int(c) for c in args.chapters.split(",")]
            else:
                chapters = [int(args.chapters)]
        
        batch_id = submit_batch(
            client=client,
            parser=parser,
            book_name=args.book,
            model=args.model,
            use_thinking=args.thinking,
            chapters=chapters,
        )
        
        # Save batch ID for later
        save_batch_id(batch_id, args.book, output_dir)
        print(f"\nBatch ID saved. Use 'status --book {args.book}' to check progress.")
    
    elif args.command == "status":
        batch_id = get_batch_id()
        status = check_batch_status(client, batch_id)
        
        print(f"Batch: {status['id']}")
        print(f"Status: {status['status']}")
        print(f"Progress: {status['counts']['succeeded']}/{status['counts']['total']} complete")
        if status['counts']['processing'] > 0:
            print(f"Processing: {status['counts']['processing']}")
        if status['counts']['errored'] > 0:
            print(f"Errored: {status['counts']['errored']}")
    
    elif args.command == "wait":
        batch_id = get_batch_id()
        success = wait_for_batch(client, batch_id, args.poll_interval)
        
        if success:
            print("\nBatch completed successfully!")
            print(f"Run 'download --book {args.book}' to save results.")
        else:
            print("\nBatch completed with some failures.")
    
    elif args.command == "download":
        batch_id = get_batch_id()
        saved_files = download_batch_results(client, batch_id, args.book, output_dir)
        print(f"\nSaved {len(saved_files)} chapters to {output_dir / args.book.lower()}/")
    
    elif args.command == "run":
        parser = GreekTextParser(args.greek_texts)
        
        # Submit
        batch_id = submit_batch(
            client=client,
            parser=parser,
            book_name=args.book,
            model=args.model,
            use_thinking=args.thinking,
        )
        save_batch_id(batch_id, args.book, output_dir)
        
        # Wait
        print()
        success = wait_for_batch(client, batch_id, args.poll_interval)
        
        if not success:
            print("\nBatch completed with some failures.")
        
        # Download
        saved_files = download_batch_results(client, batch_id, args.book, output_dir)
        print(f"\nComplete! Saved {len(saved_files)} chapters to {output_dir / args.book.lower()}/")


if __name__ == "__main__":
    main()