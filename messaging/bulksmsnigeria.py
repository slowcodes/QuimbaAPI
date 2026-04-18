
import logging
import requests
import json
from threading import Thread

logger = logging.getLogger(__name__)

bearer_token = '397|YRXsw617DQmedW8v3Khs7CY8TQJMizXyfgRB388B4669a866'
api_token = 'quS68U49qp0w3OyH2mpwNf1xtHd4XJ8UzpjYCXZpd5G8h3p6Ftf6qEdt5qfq'
url = 'https://www.bulksmsnigeria.com/api/v2/sms'

data = {
    'from': 'Quimba',
    'to': '2348030718122',
    'body': 'Hello from Quimba Nigeria API!'
}

headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def _send_sms():
    print("sending sms")
    try:
        response = requests.post(url, json=data, headers=headers)
        result = response.json()
        print(result)
    except Exception:
        logger.exception("Failed to send BulkSMS Nigeria SMS.")


def send_sms():
    thread = Thread(target=_send_sms, daemon=True)
    thread.start()
    return thread
