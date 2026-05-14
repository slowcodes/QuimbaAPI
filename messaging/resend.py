import logging
import os
from threading import Thread
from typing import Optional

import resend
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


def _send_mail(
    to_email: str,
    subject: str,
    html: str,
    from_email: str,
) -> bool:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("Resend config missing; email not sent.")
        return False

    resend.api_key = api_key
    try:
        response = resend.Emails.send(
            {
                "from": from_email,
                "to": [to_email],
                "subject": subject,
                "html": html,
            }
        )
    except Exception:
        logger.exception("Failed to send Resend email.")
        return False

    logger.info("Resend email sent: %s", response)
    return True


def send_mail(
    to_email: Optional[str] = None,
    subject: str = "Hello World",
    html: str = "<p>Congrats on sending your <strong>first email</strong>!</p>",
    from_email: Optional[str] = None,
    background: bool = True,
):
    to_email = to_email or os.getenv("RESEND_TO_EMAIL")
    from_email = from_email or os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    if not to_email:
        logger.warning("RESEND_TO_EMAIL missing; email not sent.")
        return False

    if not background:
        return _send_mail(to_email, subject, html, from_email)

    thread = Thread(
        target=_send_mail,
        args=(to_email, subject, html, from_email),
        daemon=False,
    )
    thread.start()
    return thread
