import requests
from django.conf import settings


def send_message(msg):
    json_data = {"msgtype": "markdown", "markdown": {"content": msg}}
    requests.post(url=settings.ROBOT_URL, json=json_data)
