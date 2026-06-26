from __future__ import annotations
import json
import os
import subprocess

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from google.oauth2.service_account import Credentials
except ImportError:  # pragma: no cover - exercised in test envs without google libs
    build = None  # type: ignore[assignment]
    MediaIoBaseDownload = None  # type: ignore[assignment]
    Credentials = None  # type: ignore[assignment]


def download_audio(file_id: str, dest_path: str, creds_json: str) -> str:
    try:
        if build is None or MediaIoBaseDownload is None or Credentials is None:
            raise RuntimeError("google api client libraries are not installed")
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


def main(argv: list[str] | None = None) -> int:
    """CLI: download a Drive file and convert it to 16 kHz mono WAV.

    Reads service-account credentials from GOOGLE_SERVICE_ACCOUNT_JSON.

    Example:
        python -m tools.sg_drive_download <file_id> --out /tmp/sg-job-X.wav
    """
    import argparse
    import sys

    p = argparse.ArgumentParser(description="Download a Drive audio file and convert to WAV")
    p.add_argument("file_id")
    p.add_argument("--out", required=True, help="Output WAV path (16 kHz mono)")
    args = p.parse_args(argv)

    creds_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        print("GOOGLE_SERVICE_ACCOUNT_JSON is not set", file=sys.stderr)
        return 1

    src_path = args.out + ".src"
    try:
        download_audio(args.file_id, src_path, creds_json)
        # Convert whatever container/codec Drive returned into pipeline-standard WAV.
        # Capture stderr so a conversion failure produces an actionable error the
        # orchestrator can log, instead of an opaque non-zero exit.
        proc = subprocess.run(
            ["ffmpeg", "-y", "-i", src_path, "-ar", "16000", "-ac", "1", args.out],
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            tail = (proc.stderr or "").strip()[-2000:]
            raise RuntimeError(f"ffmpeg conversion failed (exit {proc.returncode}): {tail}")
    finally:
        # The downloaded original can be large (full recording); never leave it behind.
        try:
            os.remove(src_path)
        except OSError:
            pass
    print(f"downloaded + converted → {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
