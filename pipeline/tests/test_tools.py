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
