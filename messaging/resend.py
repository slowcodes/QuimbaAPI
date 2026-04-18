import logging
from threading import Thread

import resend

logger = logging.getLogger(__name__)

resend.api_key = "re_GtQFgWAm_7dbx58t5ezJdFD6SEpeWywWn"


def _send_mail():
    print("sending email message")
    try:
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": "kc.ezenna@gmail.com",
            "subject": "Hello World",
            "html": "<p>Congrats on sending your <strong>first email</strong>!</p>"
        })
    except Exception:
        logger.exception("Failed to send Resend email.")


def send_mail():
    thread = Thread(target=_send_mail, daemon=True)
    thread.start()
    return thread
