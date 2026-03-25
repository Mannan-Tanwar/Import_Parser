import sys
import json
from pathlib import Path
from rich.console import Console
from rich.syntax import Syntax

from parser.icedis_parser import parse_icedis_file
from vision.ollama_vision import (
    extract_text_with_layout,
    check_tesseract_installed,
    parse_image_with_ollama,
    check_ollama_running,
)

console = Console()

TEXT_EXTENSIONS  = {'.txt', '.dat', '.edi', '.csv'}
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.pdf'}


def print_json(data):
    """Pretty-print a dict as syntax-highlighted JSON to the console."""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    console.print(Syntax(json_str, "json", theme="monokai", line_numbers=False))


def structure_image_text(extracted_text, image_path, method):
    """
    Wrap raw OCR / AI-extracted image text into a consistent JSON structure.

    Args:
        extracted_text : str  — raw text returned by Tesseract or Ollama
        image_path     : str  — source file name
        method         : str  — 'tesseract' | 'ollama'

    Returns:
        dict — JSON-serialisable result
    """
    lines = [l for l in extracted_text.splitlines() if l.strip()]

    return {
        "source":           str(image_path),
        "extraction_method": method,
        "total_characters": len(extracted_text),
        "total_lines":      len(lines),
        "extracted_text":   extracted_text,          # full raw text, unchanged
        "lines":            lines,                   # one entry per non-blank line
    }


def main():
    if len(sys.argv) < 2:
        console.print("[bold red]Usage:[/bold red]")
        console.print("  python main.py <file>        # parse a text file → JSON")
        console.print("  python main.py <file> --ai   # AI vision model  → JSON  (images only)")
        console.print("\nSupported file types:")
        console.print("  Text:  .txt .dat .edi .csv")
        console.print("  Image: .png .jpg .jpeg .pdf")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    use_ai    = '--ai' in sys.argv

    if not file_path.exists():
        console.print(f"[red]File not found: {file_path}[/red]")
        sys.exit(1)

    ext = file_path.suffix.lower()

    # ── Path A: Text file → ICEDIS parser → JSON ─────────────
    if ext in TEXT_EXTENSIONS:
        console.print(f"\n[bold]Parsing ICEDIS text file:[/bold] {file_path.name}\n")
        raw_text = file_path.read_text(encoding='utf-8', errors='replace')
        result   = parse_icedis_file(raw_text)
        print_json(result)

    # ── Path B: Image → extract text → JSON ──────────────────
    elif ext in IMAGE_EXTENSIONS:
        if use_ai:
            console.print(f"\n[bold]AI vision parsing:[/bold] {file_path.name}\n")

            is_running, model_ok, msg = check_ollama_running()
            if not is_running or not model_ok:
                console.print(f"[red]{msg}[/red]")
                sys.exit(1)

            extracted_text = parse_image_with_ollama(file_path)
            result = structure_image_text(extracted_text, file_path.name, method="ollama")

        else:
            console.print(f"\n[bold]Tesseract OCR parsing:[/bold] {file_path.name}\n")

            is_installed, msg = check_tesseract_installed()
            if not is_installed:
                console.print(f"[red]{msg}[/red]")
                sys.exit(1)

            extracted_text = extract_text_with_layout(file_path)
            result = structure_image_text(extracted_text, file_path.name, method="tesseract")

        print_json(result)

    else:
        console.print(f"[red]Unsupported file type: {ext}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()