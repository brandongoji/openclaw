#!/usr/bin/env python3
import argparse
import glob
import os
import pathlib
import shutil
import sys


def ensure_ffmpeg_on_path() -> None:
    if shutil.which("ffmpeg"):
        return

    candidates: list[str] = []

    # Winget install path (common on this machine)
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        candidates.extend(
            glob.glob(
                os.path.join(
                    local,
                    "Microsoft",
                    "WinGet",
                    "Packages",
                    "Gyan.FFmpeg_*",
                    "ffmpeg-*-full_build",
                    "bin",
                )
            )
        )

    # Chocolatey fallback
    candidates.append(r"C:\ProgramData\chocolatey\bin")

    # Typical manual install fallback
    candidates.append(r"C:\ffmpeg\bin")

    for p in candidates:
        if p and pathlib.Path(p, "ffmpeg.exe").exists():
            os.environ["PATH"] = p + os.pathsep + os.environ.get("PATH", "")
            if shutil.which("ffmpeg"):
                return


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", default="base")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    ensure_ffmpeg_on_path()

    if not shutil.which("ffmpeg"):
        print(
            "local whisper transcription failed: ffmpeg not found on PATH (required by whisper)",
            file=sys.stderr,
        )
        return 1

    try:
        import whisper  # type: ignore
    except Exception as e:
        print(f"Whisper runtime missing. Install with: python -m pip install openai-whisper. Details: {e}", file=sys.stderr)
        return 2

    try:
        model = whisper.load_model(args.model)
        result = model.transcribe(
            args.input,
            language=args.language,
            fp16=False,
            temperature=0,
            best_of=5,
            beam_size=5,
            condition_on_previous_text=True,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
            no_speech_threshold=0.5,
        )
        text = (result.get("text") or "").strip()
        print(text)
        return 0
    except Exception as e:
        print(f"local whisper transcription failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
