import logging
import os
from typing import Optional

import requests

logger = logging.getLogger(__name__)


def send_lab_result_ready_email(
    client_email: str,
    client_name: str,
    booking_id: int,
    lab_name: Optional[str] = None,
) -> bool:
    api_key = os.getenv("MAILGUN_API_KEY")
    domain = os.getenv("MAILGUN_DOMAIN")
    from_email = os.getenv("MAILGUN_FROM_EMAIL")
    from_name = os.getenv("MAILGUN_FROM_NAME", "Lab")

    if not api_key or not domain or not from_email:
        logger.warning("Mailgun config missing; email not sent.")
        return False

    subject = "Your lab result is ready"
    greeting_name = client_name.strip() or "Client"
    lab_line = f"{lab_name} has" if lab_name else "We have"
    text = (
        f"Hello {greeting_name},\n\n"
        f"{lab_line} completed your lab result.\n"
        f"Booking ID: {booking_id}\n\n"
        "Please log in to your account to view the full report.\n\n"
        "Thank you."
    )

    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"{from_name} <{from_email}>",
                "to": [client_email],
                "subject": subject,
                "text": text,
            },
            timeout=10,
        )
    except requests.RequestException:
        logger.exception("Failed to send Mailgun email.")
        return False

    if not response.ok:
        logger.error(
            "Mailgun email failed: status=%s body=%s",
            response.status_code,
            response.text,
        )
        return False

    return True
