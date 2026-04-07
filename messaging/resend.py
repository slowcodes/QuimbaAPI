# re_GtQFgWAm_7dbx58t5ezJdFD6SEpeWywWn

import resend

resend.api_key = "re_GtQFgWAm_7dbx58t5ezJdFD6SEpeWywWn"

def send_mail():

    r = resend.Emails.send({
        "from": "onboarding@resend.dev",
        "to": "kc.ezenna@gmail.com",
        "subject": "Hello World",
        "html": "<p>Congrats on sending your <strong>first email</strong>!</p>"
    })