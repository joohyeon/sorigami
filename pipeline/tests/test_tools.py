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
         patch("tools.sg_drive_download.subprocess.run") as mock_run, \
         patch.dict(os.environ, {"GOOGLE_SERVICE_ACCOUNT_JSON": json.dumps({"type": "service_account"})}):
        from tools.sg_drive_download import main
        rc = main(["file123", "--out", str(out_wav)])
    assert rc == 0
    mock_dl.assert_called_once()
    # ffmpeg invoked to produce the wav target
    ffmpeg_cmd = mock_run.call_args[0][0]
    assert ffmpeg_cmd[0] == "ffmpeg"
    assert str(out_wav) in ffmpeg_cmd


def test_update_job_status(mock_supabase_client):
    from tools.sg_supabase_write import update_job_status
    update_job_status("job-123", "executing")
    mock_supabase_client.table.assert_called_with("sg_jobs")
    mock_supabase_client.table.return_value.update.assert_called_once()
    mock_supabase_client.table.return_value.update.return_value.eq.assert_called_with("id", "job-123")


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
