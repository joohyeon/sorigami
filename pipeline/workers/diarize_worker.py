"""Modal GPU worker: pyannote.audio speaker diarization."""
from __future__ import annotations

try:
    import modal
    _modal_available = True
except ImportError:  # not installed outside Modal container
    modal = None  # type: ignore[assignment]
    _modal_available = False

try:
    from pyannote.audio import Pipeline
except ImportError:  # only available inside Modal image
    class Pipeline:  # type: ignore[no-redef]
        """Stub so patch("workers.diarize_worker.Pipeline.from_pretrained") works in tests."""
        @classmethod
        def from_pretrained(cls, *args, **kwargs):
            raise ImportError("pyannote.audio not installed")

_SPEAKER_LABELS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _diarize_impl(wav_path: str, num_speakers: int = 2) -> list[dict]:
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=True,
        cache_dir="/models/pyannote",
    )
    diarization = pipeline(wav_path, num_speakers=num_speakers)
    speaker_map: dict[str, str] = {}
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        if speaker not in speaker_map:
            idx = len(speaker_map)
            # Fall back to "SPK_N" when more than 26 speakers are detected
            speaker_map[speaker] = _SPEAKER_LABELS[idx] if idx < len(_SPEAKER_LABELS) else f"SPK_{idx}"
        segments.append({
            "start": round(turn.start, 3),
            "end": round(turn.end, 3),
            "speaker": speaker_map[speaker],
        })
    return segments


diarize = _diarize_impl


def _wav_duration_seconds(wav_path: str) -> float:
    """Read a WAV's duration from its header (no torch/audio deps required)."""
    import wave

    with wave.open(wav_path, "rb") as w:
        frames = w.getnframes()
        rate = w.getframerate() or 1
    return round(frames / float(rate), 3)


def diarize_local(wav_path: str, num_speakers: int = 2) -> list[dict]:
    """Deterministic local diarization with graceful degradation.

    Tries pyannote locally; only when pyannote/torch are **not installed**
    (`ImportError` — the common case on a dev machine without the GPU stack)
    does it fall back to a single speaker "A" covering the whole file, tagged
    `degraded: True` so callers can tell diarization did not actually run.

    Other failures — a missing/invalid HF token, a corrupt model cache, a
    malformed WAV, CUDA OOM — surface as `OSError`/`RuntimeError` from pyannote
    and are deliberately **propagated**, not masked, so the job fails loudly
    instead of recording a fabricated single-speaker result.
    """
    try:
        return _diarize_impl(wav_path, num_speakers=num_speakers)
    except ImportError as exc:  # torch/pyannote genuinely absent (dev box without GPU stack)
        duration = _wav_duration_seconds(wav_path)
        print(f"[diarize_local] pyannote/torch unavailable; degrading to single speaker ({exc})")
        return [{"start": 0.0, "end": duration, "speaker": _SPEAKER_LABELS[0], "degraded": True}]


def main(argv: list[str] | None = None) -> int:
    """CLI: diarize a WAV locally (with single-speaker fallback) and write JSON.

    Example:
        python -m workers.diarize_worker audio.wav --out spk.json --num-speakers 2
    """
    import argparse
    import json
    import sys

    p = argparse.ArgumentParser(description="Local pyannote diarization (degrades gracefully)")
    p.add_argument("wav_path")
    p.add_argument("--out", help="Output JSON path (default: stdout)")
    p.add_argument("--num-speakers", type=int, default=2)
    args = p.parse_args(argv)

    segments = diarize_local(args.wav_path, num_speakers=args.num_speakers)
    payload = json.dumps(segments, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(payload)
        print(f"wrote {len(segments)} speaker segments to {args.out}", file=sys.stderr)
    else:
        print(payload)
    return 0


if _modal_available:
    app = modal.App("sg-diarize")

    image = (
        modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04", add_python="3.12")
        .apt_install("ffmpeg", "libsndfile1")
        .pip_install(
            "torch==2.5.1", "torchaudio==2.5.1",
            "pyannote.audio==3.3.2", "speechbrain==1.0.2",
        )
    )

    models_volume = modal.Volume.from_name("sg-models", create_if_missing=True)
    secrets = [modal.Secret.from_name("huggingface-secret")]  # HF_TOKEN for pyannote

    @app.function(
        image=image,
        gpu="T4",
        volumes={"/models": models_volume},
        secrets=secrets,
        timeout=600,
    )
    def diarize_remote(wav_path: str, num_speakers: int = 2) -> list[dict]:
        return _diarize_impl(wav_path, num_speakers)


if __name__ == "__main__":
    raise SystemExit(main())
