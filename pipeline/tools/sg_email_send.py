from __future__ import annotations

import os
import smtplib
from datetime import datetime, UTC
from email.message import EmailMessage


REQUIRED_SMTP_ENV = (
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_FROM",
)


def send_email(recipients: list[str], subject: str, body_markdown: str) -> dict:
    if not recipients:
        raise RuntimeError("At least one recipient is required")

    config = _read_smtp_config()
    message = EmailMessage()
    message["From"] = config["from_address"]
    message["To"] = ", ".join(recipients)
    message["Subject"] = subject
    message.set_content(body_markdown)

    smtp = None
    try:
        smtp = smtplib.SMTP(config["host"], config["port"], timeout=30)
        if config["use_tls"]:
            smtp.starttls()
        smtp.login(config["username"], config["password"])
        smtp.send_message(message)
    except Exception as exc:
        raise RuntimeError(f"SMTP send failed: {_sanitize_error(exc, config['password'])}") from None
    finally:
        if smtp is not None:
            try:
                smtp.quit()
            except Exception:
                pass

    return {
        "status": "sent",
        "recipients": recipients,
        "subject": subject,
        "sent_at": datetime.now(UTC).isoformat(),
    }


def _read_smtp_config() -> dict:
    missing = [name for name in REQUIRED_SMTP_ENV if not os.environ.get(name)]
    if missing:
        raise RuntimeError(f"Missing SMTP env: {', '.join(missing)}")

    try:
        port = int(os.environ["SMTP_PORT"])
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT must be an integer") from exc

    use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() not in {"false", "0", "no"}
    return {
        "host": os.environ["SMTP_HOST"],
        "port": port,
        "username": os.environ["SMTP_USERNAME"],
        "password": os.environ["SMTP_PASSWORD"],
        "from_address": os.environ["SMTP_FROM"],
        "use_tls": use_tls,
    }


def _sanitize_error(exc: Exception, password: str) -> str:
    message = str(exc)
    if password:
        message = message.replace(password, "[redacted]")
    return f"{type(exc).__name__}: {message}"
