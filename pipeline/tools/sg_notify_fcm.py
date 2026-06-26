from __future__ import annotations
import json
import httpx
from types import SimpleNamespace

try:
    import google.auth
    import google.auth.transport.requests
    from google.oauth2 import service_account
except ImportError:  # pragma: no cover - exercised in test envs without google libs
    class _DummyRequest:
        pass

    google = SimpleNamespace(  # type: ignore[assignment]
        auth=SimpleNamespace(
            transport=SimpleNamespace(
                requests=SimpleNamespace(Request=_DummyRequest)
            )
        )
    )

    class _DummyCredentials:
        token = None

        @classmethod
        def from_service_account_info(cls, *args, **kwargs):
            raise RuntimeError("google auth libraries are not installed")

        def refresh(self, request):
            raise RuntimeError("google auth libraries are not installed")

    service_account = SimpleNamespace(Credentials=_DummyCredentials)  # type: ignore[assignment]


def send_fcm(device_token: str, title: str, body: str, creds_json: str) -> None:
    """Send FCM push via HTTP v1 API using service account credentials."""
    try:
        info = json.loads(creds_json)
        project_id = info["project_id"]

        # Get OAuth2 access token
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
        creds.refresh(google.auth.transport.requests.Request())

        url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "message": {
                "token": device_token,
                "notification": {"title": title, "body": body},
            }
        }

        resp = httpx.post(url, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
    except httpx.TimeoutException as exc:
        raise RuntimeError(f"FCM notification timed out: {exc}") from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f"FCM notification failed ({exc.response.status_code}): {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"FCM notification error: {exc}") from exc
