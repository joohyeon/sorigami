"""Modal GPU worker: faster-whisper large-v3 transcription."""
from __future__ import annotations

try:
    import modal
    _modal_available = True
except ImportError:  # not installed outside Modal container
    modal = None  # type: ignore[assignment]
    _modal_available = False

try:
    from faster_whisper import WhisperModel
except ImportError:  # only available inside Modal image
    WhisperModel = None  # type: ignore[assignment,misc]

INITIAL_PROMPT = (
    "인터뷰에서 다음 용어가 등장할 수 있습니다: "
    "Analyzing Photos, not working, iCloud, Face ID, Live Text."
)


def _transcribe_impl(
    wav_path: str,
    language: str = "ko",
    model_size: str = "large-v3",
    device: str = "cuda",
    compute_type: str = "float16",
    download_root: str | None = "/models/faster-whisper",
) -> list[dict]:
    if WhisperModel is None:
        raise RuntimeError(
            "faster-whisper is not installed. "
            "This function must run inside a Modal container or install faster-whisper locally."
        )
    model = WhisperModel(
        model_size,
        device=device,
        compute_type=compute_type,
        download_root=download_root,
    )
    segments, _ = model.transcribe(
        wav_path,
        language=language,
        task="transcribe",
        beam_size=5,
        best_of=5,
        temperature=0.0,
        condition_on_previous_text=False,
        initial_prompt=INITIAL_PROMPT if language == "ko" else None,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        word_timestamps=False,
    )
    return [
        {"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(), "avg_logprob": round(s.avg_logprob, 6)}
        for s in segments
    ]


transcribe = _transcribe_impl


def transcribe_local(
    wav_path: str, language: str = "ko", model_size: str = "large-v3"
) -> list[dict]:
    """Deterministic local transcription — faster-whisper on CPU (int8), no GPU/Modal.

    Uses the system HuggingFace cache (download_root=None) so the model is
    fetched once and reused across runs.
    """
    return _transcribe_impl(
        wav_path,
        language=language,
        model_size=model_size,
        device="cpu",
        compute_type="int8",
        download_root=None,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI: transcribe a WAV locally and write a JSON segment list.

    Example:
        python -m workers.whisper_worker audio.wav --out segs.json --language ko
    """
    import argparse
    import json
    import sys

    p = argparse.ArgumentParser(description="Local faster-whisper transcription")
    p.add_argument("wav_path")
    p.add_argument("--out", help="Output JSON path (default: stdout)")
    p.add_argument("--language", default="ko")
    p.add_argument("--model", default="large-v3", help="faster-whisper model size")
    args = p.parse_args(argv)

    segments = transcribe_local(args.wav_path, language=args.language, model_size=args.model)
    payload = json.dumps(segments, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(payload)
        print(f"wrote {len(segments)} segments to {args.out}", file=sys.stderr)
    else:
        print(payload)
    return 0

if _modal_available:
    app = modal.App("sg-whisper")

    image = (
        modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.12")
        .apt_install("ffmpeg")
        .pip_install("faster-whisper==1.1.1", "numpy<2.3")
    )

    models_volume = modal.Volume.from_name("sg-models", create_if_missing=True)

    @app.function(
        image=image,
        gpu="T4",
        volumes={"/models": models_volume},
        timeout=600,
    )
    def transcribe_remote(wav_path: str, language: str = "ko") -> list[dict]:
        return _transcribe_impl(wav_path, language)


if __name__ == "__main__":
    raise SystemExit(main())
