import requests


def send_message(msg):
    log_wechat_robot_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=9adc2280-d8b4-414f-ad60-0c15203f32a4'
    json_data = {
        'msgtype': 'markdown',
        'markdown': {
            'content': msg
        }
    }
    requests.post(url=log_wechat_robot_url, json=json_data)
