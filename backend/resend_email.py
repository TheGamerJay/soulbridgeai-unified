import os
import requests
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

def send_email(to_email, subject, html_content):
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "from": "SoulBridge AI <soulbridgeai.contact@gmail.com>",
        "to": [to_email],
        "subject": subject,
        "html": html_content
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        print("✅ Email sent successfully!")
    else:
        print("❌ Failed to send email:")
        print(response.status_code)
        print(response.text)
