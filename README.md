# 🎬 Speech-to-Subtitle Generator

Automatically transcribe any audio or video file and generate a properly formatted `.srt` subtitle file with **OpenAI Whisper**. It now works locally and in **Google Colab** or **Kaggle**.

---

## ✅ Features

- 🎙️ Transcribes MP4, MP3, WAV, MKV, MOV, M4A, FLAC, OGG
- ⏱️ Accurate timestamps in `HH:MM:SS,mmm` format
- ✂️ Automatic line splitting (no lines longer than 42 chars)
- 🖥️ Runs locally or in Colab/Kaggle
- 🔧 Configurable model size and output directory
- 📓 Includes a notebook-friendly Python function you can import and call directly

---

## 🛠️ Installation

### 1. Prerequisites

Install **FFmpeg** (required for audio extraction):

```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows — download from https://ffmpeg.org/download.html
```

### 2. Clone & Set Up

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Colab Setup

```bash
!apt-get -qq update
!apt-get -qq install ffmpeg
!pip install -r requirements.txt
```

Then in a notebook cell:

```python
from main import generate_subtitles

srt_path = generate_subtitles(
    input_path="/content/your_file.mp4",
    model_name="small",
    device="auto",
)

print(srt_path)
```

By default, output files are written to `/content/subtitles` when the input folder is not writable.

### 4. Kaggle Setup

In a Kaggle notebook, add this project as a dataset or upload the files, then run:

```bash
!pip install -r requirements.txt
```

Then call it from Python:

```python
from main import generate_subtitles

srt_path = generate_subtitles(
    input_path="/kaggle/input/your-dataset/your_file.mp4",
    model_name="small",
    device="auto",
)

print(srt_path)
```

If your input comes from `/kaggle/input`, the generated `.srt` is automatically saved to `/kaggle/working/subtitles`.

---

## 🚀 Usage

```bash
python main.py <input_file> [options]
```

### Basic Examples

```bash
# Transcribe a video using the default 'small' model
python main.py assets/lecture.mp4

# Use a faster model for a quick draft
python main.py assets/podcast.mp3 --model base

# Save the .srt to a custom output folder
python main.py assets/interview.wav --output ./subtitles/

# Set a shorter max line length and skip the preview
python main.py assets/video.mp4 --max-chars 38 --no-preview

# Force CPU or GPU if needed
python main.py assets/video.mp4 --device cpu
python main.py assets/video.mp4 --device cuda
```

### All Options

| Flag | Default | Description |
|------|---------|-------------|
| `input` | *(required)* | Path to audio/video file |
| `--model` | `small` | Whisper model: `tiny`, `base`, `small`, `medium`, `large` |
| `--output` | Same folder as input | Directory to save the `.srt` file |
| `--max-chars` | `42` | Max characters per subtitle line before auto-splitting |
| `--no-preview` | Off | Skip printing transcription preview to terminal |
| `--device` | `auto` | Use `auto`, `cpu`, or `cuda` |

---

## 📁 Project Structure

```
subtitle-generator/
│
├── main.py           # CLI entry point + notebook-friendly generate_subtitles()
├── utils.py          # Timestamp formatting & line splitting logic
├── requirements.txt  # Python dependencies
├── README.md         # This file
└── assets/           # Drop your test audio/video files here
```

---

## 🧠 Model Size Guide

| Model | Speed | Accuracy | VRAM needed |
|-------|-------|----------|-------------|
| `tiny` | ⚡ Fastest | ⭐⭐ | ~1 GB |
| `base` | ⚡ Fast | ⭐⭐⭐ | ~1 GB |
| `small` | 🔵 Balanced | ⭐⭐⭐⭐ | ~2 GB |
| `medium` | 🟡 Slower | ⭐⭐⭐⭐⭐ | ~5 GB |
| `large` | 🔴 Slowest | ⭐⭐⭐⭐⭐ | ~10 GB |

> **Recommendation:** `small` is the best default for most use cases. For slower Colab or CPU-only runs, start with `base`.

---

## 📄 Output Format (SRT)

```
1
00:00:00,000 --> 00:00:04,200
Welcome to today's lecture on
machine learning fundamentals.

2
00:00:04,500 --> 00:00:09,100
We'll start by covering the basics
of supervised learning.
```

---

## 🔮 Planned Features (Phase 4+)

- [ ] Translation to English from any language
- [ ] Speaker diarization (who said what)
- [ ] Streamlit drag-and-drop UI
- [ ] Batch processing (entire folder of videos)
- [ ] Burn subtitles into video with MoviePy
