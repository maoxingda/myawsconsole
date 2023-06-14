import requests


def send_message(msg):
    log_wechat_robot_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=91935d40-1fae-4b63-82c0-d60e3eebf28a'
    json_data = {
        'msgtype': 'markdown',
        'markdown': {
            'content': msg
        }
    }
    requests.post(url=log_wechat_robot_url, json=json_data)
