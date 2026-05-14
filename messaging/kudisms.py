import requests

def send_kudi_sms():
    url = "https://my.kudisms.net/api/corporate"

    payload = {
        "token": "o5lrqRucXYgzhJE6vwWt1yPx2Z0ijV3C4pLASfTsnIDQNm9Kb7eakH8MFdUOGB",
        "senderID": "Neomed",
        "recipients": "2348030718122",
        "message": "Testing right from Postman"
    }

    response = requests.post(url, data=payload)

    print("Status Code:", response.status_code)
    print("Response:", response.text)