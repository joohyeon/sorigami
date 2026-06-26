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
    def transcribe(wav_path: str, language: str = "ko") -> list[dict]:
        model = WhisperModel(
            "large-v3",
            device="cuda",
            compute_type="float16",
            download_root="/models/faster-whisper",
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

else:
    def transcribe(wav_path: str, language: str = "ko") -> list[dict]:  # type: ignore[misc]
        model = WhisperModel(
            "large-v3",
            device="cuda",
            compute_type="float16",
            download_root="/models/faster-whisper",
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
