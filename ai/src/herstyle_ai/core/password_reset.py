"""Password-reset link delivery."""

import asyncio
from email.message import EmailMessage
import smtplib
from urllib.parse import quote

from .config import Settings


def build_password_reset_link(settings: Settings, raw_token: str) -> str:
    # Keep the secret in the browser fragment so it is not sent in HTTP
    # Referer headers or recorded in frontend server access logs.
    return f"{settings.password_reset_url}#token={quote(raw_token)}"


def _send_password_reset_email(
    settings: Settings,
    recipient: str,
    reset_link: str,
) -> None:
    if not settings.smtp_host or not settings.smtp_from_email:
        raise RuntimeError("SMTP password-reset delivery is not configured")

    message = EmailMessage()
    message["Subject"] = "Khôi phục mật khẩu HerStyleAI"
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message.set_content(
        "Bạn vừa yêu cầu khôi phục mật khẩu HerStyleAI.\n\n"
        f"Mở liên kết sau để đặt mật khẩu mới (hết hạn sau "
        f"{settings.password_reset_token_expire_minutes} phút):\n{reset_link}\n\n"
        "Nếu bạn không yêu cầu, hãy bỏ qua email này."
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password or "")
        smtp.send_message(message)


async def deliver_password_reset_email(
    settings: Settings,
    recipient: str,
    reset_link: str,
) -> None:
    await asyncio.to_thread(
        _send_password_reset_email,
        settings,
        recipient,
        reset_link,
    )
