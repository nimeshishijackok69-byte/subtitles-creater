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

from utils import format_timestamp, split_long_line
from datetime import datetime

# ──────────────────────────────────────────────
# SUPPORTED FORMATS
# ──────────────────────────────────────────────

SUPPORTED_EXTENSIONS = {".mp4", ".mp3", ".wav", ".m4a", ".mkv", ".mov", ".flac", ".ogg"}

VALID_MODELS = ["tiny", "base", "small", "medium", "large"]
VALID_DEVICES = ["auto", "cpu", "cuda"]


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


def detect_runtime() -> str:
    """Returns the current runtime environment."""
    if os.path.exists("/kaggle/working"):
        return "kaggle"
    if os.path.exists("/content"):
        return "colab"
    return "local"


def is_writable_directory(path: str) -> bool:
    """Returns True when the directory exists and is writable."""
    return os.path.isdir(path) and os.access(path, os.W_OK)


def resolve_output_dir(input_path: str, output_dir: str = None) -> str:
    """
    Chooses a writable output directory.

    - Respects --output when provided.
    - Keeps local behavior of writing next to the input file when possible.
    - Falls back to notebook-friendly writable folders on Kaggle/Colab.
    """
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    input_dir = os.path.dirname(os.path.abspath(input_path))
    if is_writable_directory(input_dir):
        return input_dir

    runtime = detect_runtime()
    if runtime == "kaggle":
        fallback_dir = "/kaggle/working/subtitles"
    elif runtime == "colab":
        fallback_dir = "/content/subtitles"
    else:
        fallback_dir = os.path.join(os.getcwd(), "subtitles")

    os.makedirs(fallback_dir, exist_ok=True)
    return fallback_dir


def resolve_device(device: str = "auto") -> str:
    """Resolves the execution device, preferring CUDA when available."""
    try:
        import torch
    except ModuleNotFoundError:
        if device == "cuda":
            print("[WARN] CUDA was requested but PyTorch is not installed yet. Falling back to CPU.")
        return "cpu"

    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        print("[WARN] CUDA was requested but no GPU is available. Falling back to CPU.")
        return "cpu"
    return device


def transcribe_audio(file_path: str, model_size: str, device: str = "auto") -> dict:
    """
    Loads the specified Whisper model and transcribes the given file.
    Returns the full result dictionary from Whisper.
    """
    try:
        import whisper
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency: install requirements first with 'pip install -r requirements.txt'."
        ) from exc

    resolved_device = resolve_device(device)
    print(f"\n[INFO] Loading Whisper '{model_size}' model...")
    print(f"[INFO] Runtime: {detect_runtime()} | Device: {resolved_device}")
    model = whisper.load_model(model_size, device=resolved_device)

    print(f"[INFO] Transcribing: {os.path.basename(file_path)}")
    print("    (This may take a moment depending on file length and your hardware)\n")

    result = model.transcribe(file_path, verbose=False, fp16=(resolved_device == "cuda"))
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

    resolved_output_dir = resolve_output_dir(input_path, output_dir)
    output_path = os.path.join(resolved_output_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    return output_path


def print_preview(segments: list, num_lines: int = 5) -> None:
    """Prints a short preview of the transcription to the terminal."""
    print("-" * 50)
    print("TRANSCRIPTION PREVIEW (first few segments):")
    print("-" * 50)
    for segment in segments[:num_lines]:
        start = format_timestamp(segment["start"])
        end = format_timestamp(segment["end"])
        text = segment["text"].strip()
        print(f"  [{start} -> {end}]  {text}")
    if len(segments) > num_lines:
        print(f"  ... and {len(segments) - num_lines} more segments.")
    print("-" * 50)


def generate_subtitles(
    input_path: str,
    model_name: str = "small",
    output_dir: str = None,
    max_line_chars: int = 42,
    show_preview: bool = True,
    device: str = "auto",
) -> str:
    """
    Notebook-friendly wrapper that validates input, transcribes, and writes the SRT file.
    Returns the path to the generated subtitle file.
    """
    validate_input(input_path)
    result = transcribe_audio(input_path, model_name, device=device)
    segments = result.get("segments", [])

    if not segments:
        raise RuntimeError("No speech detected in the audio. Please check your file.")

    print(f"[OK] Transcription complete. {len(segments)} segments found.")

    if show_preview:
        print_preview(segments)

    srt_content = build_srt_content(segments, max_line_chars=max_line_chars)
    srt_path = export_srt(srt_content, input_path, model_name, output_dir)
    print(f"\n[OK] SRT file saved to: {srt_path}")
    return srt_path


# ──────────────────────────────────────────────
# CLI ARGUMENT PARSER
# ──────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automated Speech-to-Subtitle Generator",
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
    parser.add_argument(
        "--device",
        choices=VALID_DEVICES,
        default="auto",
        help="Execution device: auto, cpu, or cuda (default: auto)."
    )

    return parser.parse_args()


# ──────────────────────────────────────────────
# MAIN ENTRY POINT
# ──────────────────────────────────────────────

def main():
    args = parse_args()

    print("\n" + "=" * 50)
    print("  Speech-to-Subtitle Generator")
    print("=" * 50)

    try:
        generate_subtitles(
            input_path=args.input,
            model_name=args.model,
            output_dir=args.output,
            max_line_chars=args.max_chars,
            show_preview=not args.no_preview,
            device=args.device,
        )
        print("=" * 50 + "\n")
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
