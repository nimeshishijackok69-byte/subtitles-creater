"""
main.py - Automated Speech-to-Subtitle Generator (CLI)

Usage:
    python main.py <audio_or_video_file> [options]

Examples:
    python main.py assets/lecture.mp4
    python main.py assets/podcast.mp3 --model small
    python main.py assets/interview.wav --model base --output ./subtitles/
"""

import os
import sys
import argparse
import whisper

from utils import format_timestamp, split_long_line
from datetime import datetime

# ──────────────────────────────────────────────
# SUPPORTED FORMATS
# ──────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".mp4", ".mp3", ".wav", ".m4a", ".mkv", ".mov", ".flac", ".ogg"}

VALID_MODELS = ["tiny", "base", "small", "medium", "large"]


# ──────────────────────────────────────────────
# CORE FUNCTIONS
# ──────────────────────────────────────────────

def validate_input(file_path: str) -> None:
    """Checks that the input file exists and is a supported format."""
    if not os.path.isfile(file_path):
        print(f"[ERROR] File not found: '{file_path}'")
        sys.exit(1)

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"[ERROR] Unsupported file type: '{ext}'")
        print(f"        Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
        sys.exit(1)


def transcribe_audio(file_path: str, model_size: str) -> dict:
    """
    Loads the specified Whisper model and transcribes the given file.
    Returns the full result dictionary from Whisper.
    """
    print(f"\n🔄  Loading Whisper '{model_size}' model...")
    model = whisper.load_model(model_size)

    print(f"🎙️  Transcribing: {os.path.basename(file_path)}")
    print("    (This may take a moment depending on file length and your hardware)\n")

    result = model.transcribe(file_path, verbose=False)
    return result


def build_srt_content(segments: list, max_line_chars: int = 42) -> str:
    """
    Takes Whisper segment output and builds a properly formatted SRT string.

    Each subtitle block has:
      - A sequential index number
      - A timestamp line: HH:MM:SS,mmm --> HH:MM:SS,mmm
      - The subtitle text (split if too long)
      - A blank line separator
    """
    srt_blocks = []

    for i, segment in enumerate(segments, start=1):
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = split_long_line(segment["text"].strip(), max_chars=max_line_chars)

        block = f"{i}\n{start} --> {end}\n{text}\n"
        srt_blocks.append(block)

    return "\n".join(srt_blocks)


def export_srt(srt_content: str, input_path: str, model_name: str, output_dir: str = None) -> str:
    """
    Writes the SRT content to a file.

    Output path logic:
      - If --output is specified, saves there.
      - Otherwise, saves in the same directory as the input file.
    """
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename: str = f"{base_name}_{model_name}_{timestamp}.srt"

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)
    else:
        input_dir = os.path.dirname(os.path.abspath(input_path))
        output_path = os.path.join(input_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return output_path


def print_preview(segments: list, num_lines: int = 5) -> None:
    """Prints a short preview of the transcription to the terminal."""
    print("─" * 50)
    print("📄  TRANSCRIPTION PREVIEW (first few segments):")
    print("─" * 50)
    for segment in segments[:num_lines]:
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].strip()
        print(f"  [{start} → {end}]  {text}")
    if len(segments) > num_lines:
        print(f"  ... and {len(segments) - num_lines} more segments.")
    print("─" * 50)


# ──────────────────────────────────────────────
# CLI ARGUMENT PARSER
# ──────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="🎬 Automated Speech-to-Subtitle Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py lecture.mp4
  python main.py podcast.mp3 --model base
  python main.py interview.wav --model small --output ./my_subtitles/
  python main.py video.mp4 --max-chars 38 --no-preview
        """
    )

    parser.add_argument(
        "input",
        help="Path to the input audio or video file."
    )
    parser.add_argument(
        "--model",
        choices=VALID_MODELS,
        default="small",
        help="Whisper model size to use (default: small)."
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="DIR",
        help="Directory to save the .srt file (default: same folder as input)."
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=42,
        metavar="N",
        help="Maximum characters per subtitle line before splitting (default: 42)."
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Skip printing the transcription preview to terminal."
    )

    return parser.parse_args()


# ──────────────────────────────────────────────
# MAIN ENTRY POINT
# ──────────────────────────────────────────────

def main():
    args = parse_args()

    print("\n" + "═" * 50)
    print("  🎬  Speech-to-Subtitle Generator")
    print("═" * 50)

    # Step 1: Validate input
    validate_input(args.input)

    # Step 2: Transcribe
    result = transcribe_audio(args.input, args.model)
    segments = result.get("segments", [])

    if not segments:
        print("[ERROR] No speech detected in the audio. Please check your file.")
        sys.exit(1)

    print(f"✅  Transcription complete. {len(segments)} segments found.")

    # Step 3: Preview
    if not args.no_preview:
        print_preview(segments)

    # Step 4: Build SRT
    srt_content = build_srt_content(segments, max_line_chars=args.max_chars)

    # Step 5: Export
    srt_path = export_srt(srt_content, args.input, args.model, args.output)

    print(f"\n✅  SRT file saved to: {srt_path}")
    print("═" * 50 + "\n")


if __name__ == "__main__":
    main()