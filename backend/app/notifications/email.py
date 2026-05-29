import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)

_STATUS_COLOR = {
    "DOWN": "#dc2626",
    "UP": "#16a34a",
    "DEGRADED": "#d97706",
}

_STATUS_EMOJI = {
    "DOWN": "🔴",
    "UP": "🟢",
    "DEGRADED": "🟡",
}


def _build_html(subject: str, heading: str, body_lines: list[str], color: str) -> str:
    lines = "".join(f"<p style='margin:4px 0;color:#374151'>{l}</p>" for l in body_lines)
    return f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
      <div style="background:{color};padding:16px 24px;border-radius:8px 8px 0 0">
        <h2 style="color:#fff;margin:0">{heading}</h2>
      </div>
      <div style="background:#f9fafb;padding:16px 24px;border-radius:0 0 8px 8px;border:1px solid #e5e7eb">
        {lines}
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:16px 0">
        <p style="font-size:12px;color:#9ca3af">StatusForge — automated alert</p>
      </div>
    </div>
    """


async def send_incident_email(to_addresses: list[str], service_name: str, status: str, incident_title: str) -> None:
    if not to_addresses:
        return

    emoji = _STATUS_EMOJI.get(status, "⚠️")
    color = _STATUS_COLOR.get(status, "#6b7280")
    subject = f"{emoji} {service_name} is {status}"
    heading = subject

    body_lines = [
        f"<strong>Service:</strong> {service_name}",
        f"<strong>Status:</strong> {status}",
        f"<strong>Incident:</strong> {incident_title}",
    ]

    html = _build_html(subject, heading, body_lines, color)

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(to_addresses)
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user or None,
            password=settings.smtp_password or None,
            use_tls=settings.smtp_use_tls,
        )
        logger.info("Email sent to %d recipients: %s", len(to_addresses), subject)
    except Exception as e:
        logger.error("Failed to send email: %s", e)
