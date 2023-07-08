import os

# 公共配置
SESSION_VAR_SUFFIX = '__'
ROBOT_URL = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=91935d40-1fae-4b63-82c0-d60e3eebf28a'
AWS_DMS_URL = 'https://cn-northwest-1.console.amazonaws.cn/dms/v2/home?region=cn-northwest-1'
AWS_REDSHIFT_URL = 'https://cn-northwest-1.console.amazonaws.cn/redshiftv2/home?region=cn-northwest-1'
MY_AWS_URL = 'http://127.0.0.1:8000' if os.getlogin() == 'root' else 'http://127.0.0.1:8089'
ENDPOINT_SUFFIX = '80e90ae7-2ecf-49ac-bf79-ce32b8cbcc00'
REPLICATION_TASK_SUFFIX = 'bee402e5-677d-40c8-ac63-0e111007d104'
