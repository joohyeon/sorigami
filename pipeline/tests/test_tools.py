import json
import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_supabase_client():
    mock_client = MagicMock()
    with patch("tools.sg_supabase_write.create_client", return_value=mock_client), \
         patch.dict(os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_SERVICE_ROLE_KEY": "test-key"}):
        yield mock_client


def test_transcribe_returns_segments():
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 2.5
    mock_segment.text = "안녕하세요"
    mock_segment.avg_logprob = -0.3

    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], MagicMock(language="ko"))

    with patch("workers.whisper_worker.WhisperModel", return_value=mock_model):
        from workers.whisper_worker import transcribe
        result = transcribe("/tmp/test.wav")

    assert len(result) == 1
    assert result[0]["text"] == "안녕하세요"
    assert result[0]["start"] == 0.0
    assert result[0]["end"] == 2.5

def test_diarize_returns_speaker_segments():
    mock_pipeline = MagicMock()
    mock_turn = MagicMock()
    mock_turn.start = 0.0
    mock_turn.end = 3.0
    mock_diarization = mock_pipeline.return_value.return_value
    mock_diarization.itertracks.return_value = [(mock_turn, None, "SPEAKER_00")]

    with patch("workers.diarize_worker.Pipeline.from_pretrained", return_value=mock_pipeline()):
        from workers.diarize_worker import diarize
        result = diarize("/tmp/test.wav")

    assert len(result) == 1
    assert result[0]["speaker"] == "A"
    assert result[0]["start"] == 0.0


def test_transcribe_local_uses_cpu_int8():
    """The deterministic local path must run faster-whisper on CPU (int8), no CUDA."""
    mock_segment = MagicMock(start=0.0, end=2.5, text=" 안녕 ", avg_logprob=-0.3)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], MagicMock(language="ko"))

    with patch("workers.whisper_worker.WhisperModel", return_value=mock_model) as mk:
        from workers.whisper_worker import transcribe_local
        result = transcribe_local("/tmp/test.wav", language="ko", model_size="small")

    # Model constructed for CPU/int8 with the requested size
    args, kwargs = mk.call_args
    assert (args and args[0] == "small") or kwargs.get("model_size_or_path") == "small"
    assert kwargs.get("device") == "cpu"
    assert kwargs.get("compute_type") == "int8"
    assert result[0]["text"] == "안녕"


def test_whisper_cli_writes_json(tmp_path):
    """`python -m workers.whisper_worker <wav> --out <json>` writes a JSON segment list."""
    out = tmp_path / "segs.json"
    with patch("workers.whisper_worker.transcribe_local",
               return_value=[{"start": 0.0, "end": 1.0, "text": "hi", "avg_logprob": -0.1}]):
        from workers.whisper_worker import main
        main(["/tmp/test.wav", "--out", str(out), "--language", "ko", "--model", "small"])
    data = json.loads(out.read_text())
    assert data == [{"start": 0.0, "end": 1.0, "text": "hi", "avg_logprob": -0.1}]


def test_diarize_local_falls_back_to_single_speaker(tmp_path):
    """When pyannote/torch are unavailable, diarize_local degrades to one speaker
    covering the whole file so the pipeline can still reach skill extraction."""
    import wave
    wav = tmp_path / "a.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000 * 3)  # 3 seconds

    def _raise(*a, **k):
        raise ImportError("pyannote.audio not installed")

    with patch("workers.diarize_worker.Pipeline.from_pretrained", side_effect=_raise):
        from workers.diarize_worker import diarize_local
        result = diarize_local(str(wav))

    assert len(result) == 1
    assert result[0]["speaker"] == "A"
    assert result[0]["start"] == 0.0
    assert abs(result[0]["end"] - 3.0) < 0.1
    # Degraded output must be tagged so downstream/users can tell diarization
    # did not actually run.
    assert result[0]["degraded"] is True


def test_diarize_local_propagates_real_errors(tmp_path):
    """A RuntimeError/OSError (bad audio, missing HF token, CUDA OOM, corrupt
    model) must NOT be masked as a single-speaker success — it must propagate so
    the job fails loudly instead of shipping wrong speaker attribution."""
    import wave
    wav = tmp_path / "a.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000)

    with patch("workers.diarize_worker.Pipeline.from_pretrained",
               side_effect=RuntimeError("HF auth token invalid")):
        from workers.diarize_worker import diarize_local
        with pytest.raises(RuntimeError, match="HF auth token invalid"):
            diarize_local(str(wav))


def test_diarize_cli_writes_json(tmp_path):
    """`python -m workers.diarize_worker <wav> --out <json>` writes speaker JSON
    (exercises the fallback path end-to-end, no mocking of duration)."""
    import wave
    wav = tmp_path / "a.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 16000 * 2)
    out = tmp_path / "spk.json"
    with patch("workers.diarize_worker.Pipeline.from_pretrained", side_effect=ImportError("x")):
        from workers.diarize_worker import main
        main([str(wav), "--out", str(out)])
    data = json.loads(out.read_text())
    assert data[0]["speaker"] == "A"
    assert data[0]["degraded"] is True


def test_download_audio_calls_drive_api():
    mock_service = MagicMock()
    mock_service.files.return_value.get_media.return_value.execute.return_value = b"audio_bytes"

    with patch("tools.sg_drive_download.build", return_value=mock_service), \
         patch("builtins.open", MagicMock()), \
         patch("tools.sg_drive_download.Credentials") as mock_creds, \
         patch("tools.sg_drive_download.MediaIoBaseDownload") as mock_dl:
        mock_creds.from_service_account_info.return_value = MagicMock()
        mock_dl.return_value.next_chunk.return_value = (MagicMock(progress=lambda: 1.0), True)
        from tools.sg_drive_download import download_audio
        result = download_audio("file123", "/tmp/audio.m4a", json.dumps({"type": "service_account"}))
    assert result == "/tmp/audio.m4a"


def test_drive_download_cli_downloads_and_converts_to_wav(tmp_path):
    """`python -m tools.sg_drive_download <id> --out x.wav` downloads then ffmpegs to WAV."""
    out_wav = tmp_path / "audio.wav"
    with patch("tools.sg_drive_download.download_audio", return_value=str(out_wav) + ".src") as mock_dl, \
         patch("tools.sg_drive_download.subprocess.run", return_value=MagicMock(returncode=0, stderr="")) as mock_run, \
         patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_JSON": json.dumps({"type": "service_account"})}):
        from tools.sg_drive_download import main
        rc = main(["file123", "--out", str(out_wav)])
    assert rc == 0
    mock_dl.assert_called_once()
    # ffmpeg invoked to produce the wav target
    ffmpeg_cmd = mock_run.call_args[0][0]
    assert ffmpeg_cmd[0] == "ffmpeg"
    assert str(out_wav) in ffmpeg_cmd


def test_drive_download_cli_surfaces_ffmpeg_stderr(tmp_path):
    """A failed ffmpeg conversion must raise an error that includes ffmpeg's
    stderr — not an opaque non-zero-exit message — so the orchestrator can act."""
    out_wav = tmp_path / "audio.wav"
    with patch("tools.sg_drive_download.download_audio", return_value=str(out_wav) + ".src"), \
         patch("tools.sg_drive_download.subprocess.run",
               return_value=MagicMock(returncode=1, stderr="Invalid data found when processing input")), \
         patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_JSON": json.dumps({"type": "service_account"})}):
        from tools.sg_drive_download import main
        with pytest.raises(RuntimeError, match="Invalid data found"):
            main(["file123", "--out", str(out_wav)])


def test_drive_download_cli_cleans_up_src_file(tmp_path):
    """The downloaded .src intermediate must be removed (even though conversion
    succeeded) so /tmp does not fill with full recordings."""
    out_wav = tmp_path / "audio.wav"
    src = str(out_wav) + ".src"

    def fake_dl(file_id, dest, creds):
        with open(dest, "wb") as f:
            f.write(b"raw")
        return dest

    with patch("tools.sg_drive_download.download_audio", side_effect=fake_dl), \
         patch("tools.sg_drive_download.subprocess.run", return_value=MagicMock(returncode=0, stderr="")), \
         patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_JSON": json.dumps({"type": "service_account"})}):
        from tools.sg_drive_download import main
        main(["file123", "--out", str(out_wav)])
    assert not os.path.exists(src)


def test_drive_download_cli_missing_creds_returns_1(tmp_path):
    with patch.dict(os.environ, {}, clear=True):
        from tools.sg_drive_download import main
        assert main(["file123", "--out", str(tmp_path / "a.wav")]) == 1


def test_update_job_status(mock_supabase_client):
    from tools.sg_supabase_write import update_job_status
    update_job_status("job-123", "executing")
    mock_supabase_client.table.assert_called_with("sg_jobs")
    mock_supabase_client.table.return_value.update.assert_called_once()
    mock_supabase_client.table.return_value.update.return_value.eq.assert_called_with("id", "job-123")


def test_write_utterances_translates_start_end_fields(mock_supabase_client):
    from tools.sg_supabase_write import write_utterances
    write_utterances("job-123", [{"start": 1.25, "end": 2.5, "text": "hello"}])
    insert_arg = mock_supabase_client.table.return_value.insert.call_args[0][0]
    assert insert_arg == [{"job_id": "job-123", "start_sec": 1.25, "end_sec": 2.5, "text": "hello"}]


def test_normalize_utterance_passthrough_and_extra_keys():
    from tools.sg_supabase_write import _normalize_utterance
    # An already-normalized row is left untouched (no double-translation).
    already = {"start_sec": 1.0, "end_sec": 2.0, "text": "hi", "speaker_id": "uuid-x"}
    assert _normalize_utterance(already) == already
    # Translation preserves unrelated keys (e.g. speaker label).
    out = _normalize_utterance({"start": 1.0, "end": 2.0, "text": "hi", "speaker": "A"})
    assert out == {"start_sec": 1.0, "end_sec": 2.0, "text": "hi", "speaker": "A"}
    # Mixed input (both _sec and plain) — old keys must be dropped to avoid unknown-column errors.
    mixed = {"start_sec": 1.0, "start": 1.0, "end_sec": 2.0, "end": 2.0, "text": "hi"}
    assert _normalize_utterance(mixed) == {"start_sec": 1.0, "end_sec": 2.0, "text": "hi"}


def test_write_speakers_returns_inserted_rows(mock_supabase_client):
    """write_speakers must return the inserted rows (with their generated ids)
    so the orchestrator can map diarization labels → sg_speakers.id for
    populating utterance.speaker_id."""
    from tools.sg_supabase_write import write_speakers
    inserted = [{"id": "uuid-1", "job_id": "job-1", "label": "A"}]
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value = MagicMock(data=inserted)
    result = write_speakers("job-1", [{"label": "A"}])
    assert result == inserted


def test_send_fcm_notification():
    from tools.sg_notify_fcm import send_fcm
    with patch("tools.sg_notify_fcm.service_account.Credentials.from_service_account_info") as mock_creds, \
         patch("tools.sg_notify_fcm.google.auth.transport.requests.Request"), \
         patch("tools.sg_notify_fcm.httpx.post") as mock_post:
        mock_creds.return_value.token = "test-token"
        mock_creds.return_value.refresh = lambda r: None
        mock_post.return_value.raise_for_status = lambda: None
        send_fcm(
            "device-token-123",
            "Test Title",
            "Test Body",
            json.dumps({"project_id": "test-proj", "type": "service_account"}),
        )
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "fcm.googleapis.com/v1" in call_args[0][0]


def test_post_slack():
    from unittest.mock import patch
    import httpx
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"ok": True})
        from tools.sg_slack_post import post_slack
        post_slack("#meetings", "Hello", "xoxb-token")
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args
    assert "slack.com" in str(call_kwargs)


def test_call_webhook():
    from unittest.mock import patch, MagicMock
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        from tools.sg_webhook_call import call_webhook
        call_webhook("https://example.com/hook", {"key": "value"})
    mock_post.assert_called_once_with(
        "https://example.com/hook",
        json={"key": "value"},
        timeout=15,
    )


def test_compute_quality_good_score():
    from tools.sg_quality import compute_quality
    segments = [
        {"start": 0.0, "end": 2.0, "text": "hello", "avg_logprob": -0.3},
        {"start": 2.0, "end": 4.0, "text": "world", "avg_logprob": -0.4},
    ]
    q = compute_quality(segments)
    assert q["transcript_score"] == "good"
    assert q["avg_logprob"] == -0.35
    assert q["segment_count"] == 2
    assert q["low_confidence_count"] == 0
    assert q["low_confidence_segments"] == []
    assert q["diarization_degraded"] is False


def test_compute_quality_fair_score():
    from tools.sg_quality import compute_quality
    segments = [
        {"start": 0.0, "end": 2.0, "text": "a", "avg_logprob": -0.6},
        {"start": 2.0, "end": 4.0, "text": "b", "avg_logprob": -0.7},
    ]
    q = compute_quality(segments)
    assert q["transcript_score"] == "fair"


def test_compute_quality_poor_score():
    from tools.sg_quality import compute_quality
    segments = [
        {"start": 0.0, "end": 2.0, "text": "a", "avg_logprob": -0.9},
        {"start": 2.0, "end": 4.0, "text": "b", "avg_logprob": -0.85},
    ]
    q = compute_quality(segments)
    assert q["transcript_score"] == "poor"


def test_compute_quality_surfaces_low_confidence_segments():
    from tools.sg_quality import compute_quality
    segs = [{"start": float(i), "end": float(i+1), "text": f"t{i}", "avg_logprob": -1.5 - i * 0.1}
            for i in range(15)]
    q = compute_quality(segs)
    assert q["low_confidence_count"] == 15
    # Only up to 10 worst segments are returned, sorted worst-first
    assert len(q["low_confidence_segments"]) == 10
    assert q["low_confidence_segments"][0]["avg_logprob"] <= q["low_confidence_segments"][-1]["avg_logprob"]


def test_compute_quality_duration_from_last_segment_end():
    from tools.sg_quality import compute_quality
    segments = [
        {"start": 0.0, "end": 10.0, "text": "hi", "avg_logprob": -0.3},
        {"start": 10.0, "end": 25.5, "text": "bye", "avg_logprob": -0.4},
    ]
    q = compute_quality(segments)
    assert q["duration_sec"] == 25.5


def test_compute_quality_empty_segments():
    from tools.sg_quality import compute_quality
    q = compute_quality([])
    assert q["transcript_score"] == "good"
    assert q["avg_logprob"] == 0.0
    assert q["segment_count"] == 0
    assert q["duration_sec"] == 0.0


def test_with_diarization_degraded():
    from tools.sg_quality import compute_quality, with_diarization_degraded
    q = compute_quality([{"start": 0.0, "end": 1.0, "text": "hi", "avg_logprob": -0.3}])
    assert q["diarization_degraded"] is False
    updated = with_diarization_degraded(q, True)
    assert updated["diarization_degraded"] is True
    # Original not mutated
    assert q["diarization_degraded"] is False


def test_compute_quality_boundary_good_to_fair():
    """avg_logprob exactly -0.5 is still 'good' (>= -0.5)."""
    from tools.sg_quality import compute_quality
    segments = [{"start": 0.0, "end": 1.0, "text": "a", "avg_logprob": -0.5}]
    assert compute_quality(segments)["transcript_score"] == "good"


def test_compute_quality_boundary_fair_to_poor():
    """avg_logprob exactly -0.8 is still 'fair' (>= -0.8)."""
    from tools.sg_quality import compute_quality
    segments = [{"start": 0.0, "end": 1.0, "text": "a", "avg_logprob": -0.8}]
    assert compute_quality(segments)["transcript_score"] == "fair"


def test_compute_quality_require_review_false_path():
    """require_review flag on skill context does not affect quality computation."""
    from tools.sg_quality import compute_quality
    segments = [{"start": 0.0, "end": 1.0, "text": "hi", "avg_logprob": -0.4}]
    q = compute_quality(segments)
    assert q["transcript_score"] == "good"
    assert "require_review" not in q
