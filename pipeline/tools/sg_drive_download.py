from __future__ import annotations
import io, json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials


def download_audio(file_id: str, dest_path: str, creds_json: str) -> str:
    try:
        info = json.loads(creds_json)
        creds = Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
        service = build("drive", "v3", credentials=creds)
        request = service.files().get_media(fileId=file_id)
        with open(dest_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return dest_path
    except Exception as exc:
        raise RuntimeError(f"Drive download failed for {file_id}: {exc}") from exc
