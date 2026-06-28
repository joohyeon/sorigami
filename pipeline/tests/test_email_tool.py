import os
import traceback
from unittest.mock import MagicMock, patch

import pytest


SMTP_ENV = {
    "SMTP_HOST": "smtp.example.com",
    "SMTP_PORT": "587",
    "SMTP_USERNAME": "user@example.com",
    "SMTP_PASSWORD": "secret-password",
    "SMTP_FROM": "noreply@example.com",
}


def test_send_email_uses_starttls_and_sends_message():
    smtp = MagicMock()
    with patch.dict(os.environ, {**SMTP_ENV, "SMTP_USE_TLS": "true"}, clear=True), \
         patch("tools.sg_email_send.smtplib.SMTP", return_value=smtp) as smtp_cls:
        from tools.sg_email_send import send_email

        result = send_email(
            recipients=["alice@example.com", "bob@example.com"],
            subject="Team Meeting follow-up",
            body_markdown="# Summary\n\nDone.",
        )

    smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=30)
    smtp.starttls.assert_called_once()
    smtp.login.assert_called_once_with("user@example.com", "secret-password")
    sent_message = smtp.send_message.call_args.args[0]
    assert sent_message["From"] == "noreply@example.com"
    assert sent_message["To"] == "alice@example.com, bob@example.com"
    assert sent_message["Subject"] == "Team Meeting follow-up"
    assert sent_message.get_content().strip() == "# Summary\n\nDone."
    smtp.quit.assert_called_once()
    assert result["recipients"] == ["alice@example.com", "bob@example.com"]
    assert result["subject"] == "Team Meeting follow-up"
    assert result["status"] == "sent"
    assert "secret-password" not in str(result)


def test_send_email_requires_smtp_env():
    with patch.dict(os.environ, {}, clear=True):
        from tools.sg_email_send import send_email

        with pytest.raises(RuntimeError, match="Missing SMTP env"):
            send_email(["alice@example.com"], "Subject", "Body")


def test_send_email_redacts_password_from_smtp_errors():
    smtp = MagicMock()
    smtp.login.side_effect = RuntimeError("bad password secret-password")
    with patch.dict(os.environ, SMTP_ENV, clear=True), \
         patch("tools.sg_email_send.smtplib.SMTP", return_value=smtp):
        from tools.sg_email_send import send_email

        with pytest.raises(RuntimeError) as err:
            send_email(["alice@example.com"], "Subject", "Body")

    assert "secret-password" not in str(err.value)
    assert "[redacted]" in str(err.value)


def test_send_email_redacts_password_from_formatted_traceback():
    smtp = MagicMock()
    smtp.login.side_effect = RuntimeError("bad password secret-password")
    with patch.dict(os.environ, SMTP_ENV, clear=True), \
         patch("tools.sg_email_send.smtplib.SMTP", return_value=smtp):
        from tools.sg_email_send import send_email

        with pytest.raises(RuntimeError) as err:
            send_email(["alice@example.com"], "Subject", "Body")

    formatted = "".join(traceback.format_exception(err.value))
    assert "secret-password" not in formatted
    assert "[redacted]" in formatted


def test_send_email_can_disable_starttls_for_local_smtp():
    smtp = MagicMock()
    with patch.dict(os.environ, {**SMTP_ENV, "SMTP_USE_TLS": "false"}, clear=True), \
         patch("tools.sg_email_send.smtplib.SMTP", return_value=smtp):
        from tools.sg_email_send import send_email

        send_email(["alice@example.com"], "Subject", "Body")

    smtp.starttls.assert_not_called()
    smtp.send_message.assert_called_once()


def test_send_email_raises_when_recipients_empty():
    with patch.dict(os.environ, SMTP_ENV, clear=True):
        from tools.sg_email_send import send_email

        with pytest.raises(RuntimeError, match="recipient"):
            send_email([], "Subject", "Body")


def test_send_email_raises_when_smtp_port_not_integer():
    bad_env = {**SMTP_ENV, "SMTP_PORT": "not-a-number"}
    with patch.dict(os.environ, bad_env, clear=True):
        from tools.sg_email_send import send_email

        with pytest.raises(RuntimeError, match="integer"):
            send_email(["alice@example.com"], "Subject", "Body")
