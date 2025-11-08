import os
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.header import decode_header
from typing import Any, Dict, List
import asyncio


class GmailService:
    """Simple Gmail service using IMAP and SMTP.

    Credentials are read from the ``GMAIL_USERNAME`` and ``GMAIL_APP_PASSWORD``
    environment variables unless explicitly provided.
    """

    def __init__(self, username: str | None = None, password: str | None = None) -> None:
        self.username = username or os.getenv("GMAIL_USERNAME")
        self.password = password or os.getenv("GMAIL_APP_PASSWORD")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _require_credentials(self) -> None:
        if not self.username or not self.password:
            raise ValueError("Missing Gmail credentials")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def check_unread(self) -> Dict[str, Any]:
        """Return unread email summary."""
        return await asyncio.to_thread(self._check_unread_sync)

    def _check_unread_sync(self) -> Dict[str, Any]:
        self._require_credentials()
        with imaplib.IMAP4_SSL("imap.gmail.com") as imap:
            imap.login(self.username, self.password)
            imap.select("inbox")
            status, messages = imap.search(None, "UNSEEN")
            if status != "OK":
                return {"unreadCount": 0, "emails": []}
            msg_nums = messages[0].split()
            emails: List[Dict[str, str]] = []
            for num in msg_nums[:5]:
                status, data = imap.fetch(num, "(RFC822)")
                if status != "OK" or not data:
                    continue
                msg = email.message_from_bytes(data[0][1])
                subject, enc = decode_header(msg.get("Subject"))[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(enc or "utf-8", errors="ignore")
                from_ = msg.get("From", "")
                snippet = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                snippet = payload[:100].decode(errors="ignore")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if isinstance(payload, bytes):
                        snippet = payload[:100].decode(errors="ignore")
                emails.append({"from": from_, "subject": subject, "snippet": snippet})
        return {"unreadCount": len(msg_nums), "emails": emails}

    async def compose_email(self, recipient: str, subject: str, body: str) -> Dict[str, Any]:
        """Send an email."""
        await asyncio.to_thread(self._compose_email_sync, recipient, subject, body)
        return {"success": True, "message": f"Email sent to {recipient}.", "body": body}

    def _compose_email_sync(self, recipient: str, subject: str, body: str) -> None:
        self._require_credentials()
        msg = MIMEText(body)
        msg["From"] = self.username
        msg["To"] = recipient
        msg["Subject"] = subject
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(self.username, self.password)
            smtp.sendmail(self.username, [recipient], msg.as_string())
