#!/usr/bin/env python3
import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--model", default="base")
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    try:
        import whisper  # type: ignore
    except Exception as e:
        print(f"Whisper runtime missing. Install with: python -m pip install openai-whisper. Details: {e}", file=sys.stderr)
        return 2

    try:
        model = whisper.load_model(args.model)
        result = model.transcribe(args.input, language=args.language)
        text = (result.get("text") or "").strip()
        print(text)
        return 0
    except Exception as e:
        print(f"local whisper transcription failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
