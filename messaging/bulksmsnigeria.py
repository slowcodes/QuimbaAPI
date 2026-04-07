
import requests
import json

api_token = '397|YRXsw617DQmedW8v3Khs7CY8TQJMizXyfgRB388B4669a866'
url = 'https://www.bulksmsnigeria.com/api/v2/sms'

data = {
    'from': 'Your Sender ID',
    'to': '2347037770033,2349050030090',
    'body': 'Hello from BulkSMS Nigeria API!'
}

headers = {
    'Authorization': f'Bearer {api_token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

response = requests.post(url, json=data, headers=headers)
result = response.js