#!/usr/bin/env python
import argparse
import sys

from moonshine_voice import get_model_for_language
from moonshine_voice.transcriber import Transcriber
from moonshine_voice.utils import load_wav_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Transcribe WAV file with Moonshine")
    parser.add_argument("--input", required=True, help="Path to WAV file")
    parser.add_argument("--language", default="en", help="Language code (default: en)")
    parser.add_argument("--model", choices=["tiny", "base"], default="tiny", help="Moonshine model size")
    args = parser.parse_args()

    model_arch = 0 if args.model == "tiny" else 1

    model_path, resolved_arch = get_model_for_language(
        wanted_language=args.language,
        wanted_model_arch=model_arch,
    )

    audio_data, sample_rate = load_wav_file(args.input)

    with Transcriber(model_path=model_path, model_arch=resolved_arch) as transcriber:
      transcript = transcriber.transcribe_without_streaming(audio_data, sample_rate)

    lines = []
    for line in getattr(transcript, "lines", []) or []:
        text = (getattr(line, "text", "") or "").strip()
        if text:
            lines.append(text)

    text = " ".join(lines).strip()
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
