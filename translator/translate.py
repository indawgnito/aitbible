#!/usr/bin/env python3
"""
Main translation script for the AIT Bible project.

Translates Greek biblical texts to English using AI models (Anthropic or Google).
"""

import os
import sys
import time
import argparse
from pathlib import Path
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

try:
    from google.genai import types
except ImportError:
    types = None

from greek_parser import GreekTextParser
from prompt_template import build_prompt
from utils import export_book_to_json
from xml_export import export_book_to_xml
from glossary_builder import build_glossary


# Configuration
DEFAULT_MODEL = "gemini-3-flash"  # Default to Gemini 3 Flash
MAX_TOKENS = 16000  # Must be > THINKING_BUDGET when thinking is enabled
THINKING_BUDGET = 10000  # Token budget for extended thinking
MAX_RETRIES = 3  # Maximum number of retries for rate limit errors
RETRY_DELAY = 2.0  # Initial delay for exponential backoff (seconds)

# Model mapping: user-friendly names to actual model IDs
MODEL_MAP = {
    # Anthropic models
    "opus-4-5": "claude-opus-4-5",
    "sonnet-4-5": "claude-sonnet-4-5",
    "claude-opus-4-5": "claude-opus-4-5",
    "claude-sonnet-4-5": "claude-sonnet-4-5",
    # Google Gemini models
    "gemini-3": "gemini-3-preview",
    "gemini-3-flash": "gemini-3-flash-preview",
    "gemini-3-preview": "gemini-3-preview",
    "gemini-3-flash-preview": "gemini-3-flash-preview",
}


def get_model_provider(model_id: str) -> str:
    """Determine which provider (anthropic or google) to use for a model."""
    if model_id.startswith("claude-"):
        return "anthropic"
    elif model_id.startswith("gemini-"):
        return "google"
    else:
        raise ValueError(f"Unknown model provider for: {model_id}")


def get_default_parallelism(model_id: str, chapter_count: int) -> int:
    """
    Determine default parallelism based on model.

    Returns:
        Number of parallel requests to use (None means unlimited)
    """
    # Gemini 3 Flash has very high rate limits (1000 RPM)
    if model_id == "gemini-3-flash-preview":
        return chapter_count  # Translate all chapters in parallel

    # All other models: 5 parallel requests
    # (gemini-3, claude-opus-4-5, claude-sonnet-4-5)
    return 5


def get_anthropic_client() -> anthropic.Anthropic:
    """Initialize the Anthropic client."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: export ANTHROPIC_API_KEY='your-key-here'")
        sys.exit(1)

    return anthropic.Anthropic(api_key=api_key)


def get_google_client():
    """Initialize the Google Gemini client."""
    try:
        from google import genai
    except ImportError:
        print("Error: google-genai package not installed.")
        print("Install it with: pip install google-genai")
        sys.exit(1)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Get your key at: https://aistudio.google.com")
        print("Set it with: export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)

    return genai.Client(api_key=api_key)


def translate_text(
    client,
    greek_text: str,
    book_name: str,
    chapter_num: int,
    start_verse: Optional[int] = None,
    end_verse: Optional[int] = None,
    model: str = DEFAULT_MODEL,
    use_thinking: bool = False,
) -> str:
    """
    Translate Greek text to English using AI model with retry logic.
    """
    # Map user-friendly model name to actual model ID
    model_id = MODEL_MAP.get(model, model)
    provider = get_model_provider(model_id)

    prompt = build_prompt(
        source_text=greek_text,
        book_name=book_name,
        chapter_num=chapter_num,
        start_verse=start_verse,
        end_verse=end_verse,
    )

    # Retry logic with exponential backoff
    for attempt in range(MAX_RETRIES):
        try:
            if provider == "anthropic":
                # Anthropic API call
                api_params = {
                    "model": model_id,
                    "max_tokens": MAX_TOKENS,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                }

                # Add extended thinking if requested
                if use_thinking:
                    api_params["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": THINKING_BUDGET,
                    }

                message = client.messages.create(**api_params)

                # Extract text from response (skip thinking blocks)
                response_text = ""
                for block in message.content:
                    if hasattr(block, "text") and block.type == "text":
                        response_text += block.text

                return response_text

            elif provider == "google":
                if types is None:
                    raise ImportError("The 'google-genai' package is required for Gemini models. Install it with: pip install google-genai")

                # Google Gemini API call                
                # Initialize empty config
                config = types.GenerateContentConfig()

                # Gemini 3 supports thinking mode via thinking_level parameter
                if use_thinking:
                    config.thinking_config = types.ThinkingConfig(
                        thinking_level="high"
                    )

                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=config,
                )

                return response.text
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        except Exception as e:
            # Check if it's a rate limit error (429)
            error_str = str(e).lower()
            is_rate_limit = "429" in error_str or "rate limit" in error_str or "quota" in error_str

            if is_rate_limit and attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                print(f"    Rate limit hit, retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})...")
                time.sleep(delay)
            else:
                # Not a rate limit error, or we've exhausted retries
                raise


def save_translation(
    translation: str,
    book_name: str,
    chapter_num: int,
    output_dir: Path,
    start_verse: Optional[int] = None,
    end_verse: Optional[int] = None,
) -> Path:
    """
    Save a translation to a text file.
    
    Returns the path to the saved file.
    """
    # Create book directory
    book_dir = output_dir / book_name.lower()
    book_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine filename
    if start_verse is not None and end_verse is not None:
        filename = f"chapter_{chapter_num:02d}_verses_{start_verse}-{end_verse}.txt"
    else:
        filename = f"chapter_{chapter_num:02d}.txt"
    
    filepath = book_dir / filename
    
    # Build file header
    header_lines = [
        f"# {book_name.title()} Chapter {chapter_num}",
    ]
    if start_verse is not None:
        header_lines.append(f"# Verses {start_verse}-{end_verse}")
    header_lines.extend([
        f"# AIT Bible Translation",
        f"# Generated by aitbible.org",
        "",
        "",
    ])
    header = "\n".join(header_lines)
    
    # Write file
    filepath.write_text(header + translation, encoding="utf-8")
    
    return filepath


def translate_chapter(
    client,
    parser: GreekTextParser,
    book_name: str,
    chapter_num: int,
    output_dir: Path,
    model: str = DEFAULT_MODEL,
    start_verse: Optional[int] = None,
    end_verse: Optional[int] = None,
    use_thinking: bool = False,
) -> Path:
    """
    Translate a single chapter (or verse range) and save it.

    Returns the path to the saved file.
    """
    print(f"Translating {book_name.title()} {chapter_num}", end="")
    if start_verse is not None:
        print(f":{start_verse}-{end_verse}", end="")
    if use_thinking:
        print(" (with extended thinking)", end="")
    print("...")
    
    # Get Greek text
    if start_verse is not None and end_verse is not None:
        greek_text = parser.get_verse_range_text(
            book_name, chapter_num, start_verse, end_verse
        )
    else:
        greek_text = parser.get_chapter_text(book_name, chapter_num)
    
    # Translate
    translation = translate_text(
        client=client,
        greek_text=greek_text,
        book_name=book_name,
        chapter_num=chapter_num,
        start_verse=start_verse,
        end_verse=end_verse,
        model=model,
        use_thinking=use_thinking,
    )
    
    # Save
    filepath = save_translation(
        translation=translation,
        book_name=book_name,
        chapter_num=chapter_num,
        output_dir=output_dir,
        start_verse=start_verse,
        end_verse=end_verse,
    )
    
    print(f"  Saved to {filepath}")
    return filepath


def translate_book(
    client,
    parser: GreekTextParser,
    book_name: str,
    output_dir: Path,
    model: str = DEFAULT_MODEL,
    use_thinking: bool = False,
    json_dir: Optional[Path] = None,
    parallel: Optional[int] = None,
    export_xml: bool = False,
) -> list[Path]:
    """
    Translate an entire book, chapter by chapter with parallel processing.
    """
    chapter_count = parser.get_chapter_count(book_name)

    # Determine parallelism
    model_id = MODEL_MAP.get(model, model)
    if parallel is None:
        parallel = get_default_parallelism(model_id, chapter_count)

    print(f"Translating {book_name.title()} ({chapter_count} chapters)")
    if use_thinking:
        print("Extended thinking enabled")
    print(f"Parallel requests: {parallel}")
    print()

    saved_files = []

    # Define a worker function for parallel execution
    def translate_chapter_worker(chapter_num: int) -> tuple[int, Path]:
        """Translate a single chapter and return (chapter_num, filepath)."""
        filepath = translate_chapter(
            client=client,
            parser=parser,
            book_name=book_name,
            chapter_num=chapter_num,
            output_dir=output_dir,
            model=model,
            use_thinking=use_thinking,
        )
        return (chapter_num, filepath)

    # Use ThreadPoolExecutor for parallel translation
    with ThreadPoolExecutor(max_workers=parallel) as executor:
        # Submit all chapters
        future_to_chapter = {
            executor.submit(translate_chapter_worker, chapter_num): chapter_num
            for chapter_num in range(1, chapter_count + 1)
        }

        # Process completed translations
        for future in as_completed(future_to_chapter):
            chapter_num = future_to_chapter[future]
            try:
                _, filepath = future.result()
                saved_files.append(filepath)
            except Exception as e:
                print(f"  ERROR: Chapter {chapter_num} failed: {e}")

    print(f"\nCompleted {book_name.title()}: {len(saved_files)} chapters translated.")

    # Auto-export for web app
    if json_dir is None:
        json_dir = Path(__file__).parent.parent / "web" / "data"

    book_dir = output_dir / book_name.lower()
    book_id = book_name.lower()
    book_display_name = book_name.title()

    if export_xml:
        xml_file = json_dir / f"{book_id}.xml"
        print(f"\nExporting to XML for web app...")
        try:
            export_book_to_xml(
                book_dir,
                xml_file,
                book_id,
                book_display_name,
                parser  # Pass the Greek parser for word/lemma data
            )
        except Exception as e:
            print(f"  Warning: XML export failed: {e}")
            print(f"  You can manually export later with: python utils.py xml {book_dir}")
    else:
        json_file = json_dir / f"{book_id}.json"
        print(f"\nExporting to JSON for web app...")
        try:
            export_book_to_json(book_dir, json_file)
        except Exception as e:
            print(f"  Warning: JSON export failed: {e}")
            print(f"  You can manually export later with: python utils.py json {book_dir}")

    # Update glossary with new terms from this translation
    print(f"\nUpdating glossary...")
    try:
        build_glossary()
    except Exception as e:
        print(f"  Warning: Glossary update failed: {e}")
        print(f"  You can manually update later with: python glossary_builder.py")

    return saved_files


def parse_verse_range(verse_str: str) -> Tuple[int, int]:
    """Parse a verse range string like '1-18' into (start, end)."""
    if "-" in verse_str:
        parts = verse_str.split("-")
        return int(parts[0]), int(parts[1])
    else:
        v = int(verse_str)
        return v, v


def main():
    arg_parser = argparse.ArgumentParser(
        description="Translate biblical Greek texts to English using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --book matthew --chapter 6
  %(prog)s --book matthew --all
  %(prog)s --new-testament --model gemini-3-flash --thinking
  %(prog)s --list-books
        """,
    )
    
    arg_parser.add_argument(
        "--book", "-b",
        help="Book name (e.g., 'matthew', 'john', '1corinthians')",
    )
    arg_parser.add_argument(
        "--chapter", "-c",
        type=int,
        help="Chapter number to translate",
    )
    arg_parser.add_argument(
        "--verses", "-v",
        help="Verse range (e.g., '1-18')",
    )
    arg_parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Translate all chapters in the book",
    )
    arg_parser.add_argument(
        "--new-testament", "--nt",
        action="store_true",
        help="Translate the entire New Testament (all available books)",
    )
    arg_parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompts (for automated/batch runs)",
    )
    arg_parser.add_argument(
        "--output", "-o",
        default="output",
        help="Output directory (default: 'output')",
    )
    arg_parser.add_argument(
        "--greek-texts", "-g",
        default="greek_texts",
        help="Greek texts directory (default: 'greek_texts')",
    )
    arg_parser.add_argument(
        "--model", "-m",
        default=DEFAULT_MODEL,
        help=f"AI model to use: opus-4-5, sonnet-4-5, gemini-3, gemini-3-flash (default: {DEFAULT_MODEL})",
    )
    arg_parser.add_argument(
        "--thinking", "-t",
        action="store_true",
        help="Enable extended thinking for more deliberate translations",
    )
    arg_parser.add_argument(
        "--json-dir", "-j",
        type=Path,
        help="JSON output directory for full books (default: ../web/data)",
    )
    arg_parser.add_argument(
        "--xml",
        action="store_true",
        help="Export to XML format (with Greek text and speaker tags) instead of JSON",
    )
    arg_parser.add_argument(
        "--parallel", "-p",
        type=int,
        help="Number of parallel requests (default: 5 for most models, all chapters for gemini-3-flash)",
    )
    arg_parser.add_argument(
        "--list-books",
        action="store_true",
        help="List available books and exit",
    )
    
    args = arg_parser.parse_args()
    
    # Initialize parser
    parser = GreekTextParser(args.greek_texts)
    
    # List books mode
    if args.list_books:
        print("Available books:")
        for book in parser.list_books():
            chapters = parser.get_chapter_count(book)
            print(f"  {book}: {chapters} chapters")
        return
    
    # Initialize client based on model
    model_id = MODEL_MAP.get(args.model, args.model)
    provider = get_model_provider(model_id)

    if provider == "anthropic":
        client = get_anthropic_client()
    elif provider == "google":
        client = get_google_client()
    else:
        print(f"Error: Unsupported model provider for {args.model}")
        sys.exit(1)

    output_dir = Path(args.output)

    # ---------------------------------------------------------
    # MODE 1: Translate Entire New Testament
    # ---------------------------------------------------------
    if args.new_testament:
        books = parser.list_books()
        total_chapters = sum(parser.get_chapter_count(b) for b in books)
        
        print("\n" + "="*60)
        print(f"  WARNING: YOU ARE ABOUT TO TRANSLATE THE ENTIRE NEW TESTAMENT")
        print("="*60)
        print(f"  - Books:        {len(books)}")
        print(f"  - Chapters:     {total_chapters}")
        print(f"  - Model:        {args.model}")
        print(f"  - Output Dir:   {output_dir.resolve()}")
        
        if args.thinking:
             print(f"  - THINKING:     ENABLED (This will significantly increase cost/tokens)")
        else:
             print(f"  - THINKING:     Disabled")
             
        if not args.yes:
            print("\nType 'Y' to confirm and proceed, or anything else to cancel.")
            confirm = input("> ")

            if confirm.strip().upper() != 'Y':
                print("Operation cancelled.")
                sys.exit(0)
            
        print("\nStarting Bulk Translation...")
        start_time = time.time()
        
        for i, book in enumerate(books, 1):
            print(f"\n[{i}/{len(books)}] Processing {book.title()}...")
            translate_book(
                client=client,
                parser=parser,
                book_name=book,
                output_dir=output_dir,
                model=args.model,
                use_thinking=args.thinking,
                json_dir=args.json_dir,
                parallel=args.parallel if hasattr(args, 'parallel') else None,
                export_xml=args.xml,
            )
            
        elapsed = time.time() - start_time
        print(f"\n\nAll operations complete in {elapsed/60:.2f} minutes.")
        return

    # ---------------------------------------------------------
    # MODE 2: Standard Book/Chapter Translation
    # ---------------------------------------------------------
    
    # Validate arguments for standard mode
    if not args.book:
        arg_parser.error("--book is required (unless using --new-testament or --list-books)")
    
    if not args.all and not args.chapter:
        arg_parser.error("Either --chapter or --all is required")
    
    # Translate
    if args.all:
        translate_book(
            client=client,
            parser=parser,
            book_name=args.book,
            output_dir=output_dir,
            model=args.model,
            use_thinking=args.thinking,
            json_dir=args.json_dir,
            parallel=args.parallel if hasattr(args, 'parallel') else None,
            export_xml=args.xml,
        )
    else:
        start_verse = None
        end_verse = None
        
        if args.verses:
            start_verse, end_verse = parse_verse_range(args.verses)
        
        translate_chapter(
            client=client,
            parser=parser,
            book_name=args.book,
            chapter_num=args.chapter,
            output_dir=output_dir,
            model=args.model,
            start_verse=start_verse,
            end_verse=end_verse,
            use_thinking=args.thinking,
        )


if __name__ == "__main__":
    main()