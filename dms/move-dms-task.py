import os
import sys
import threading
import time
from datetime import datetime

import boto3
import pytz
import requests


def process_task(task_identifier, target_replication_instance_arn):
    try:
        shanghai_tz = pytz.timezone("Asia/Shanghai")
        client = boto3.client("dms", region_name="cn-northwest-1")

        assert "arn:aws-cn:dms:cn-northwest-1:" in target_replication_instance_arn

        response = client.describe_replication_tasks(
            Filters=[
                {
                    "Name": "replication-task-id",
                    "Values": [
                        task_identifier,
                    ],
                },
            ],
            WithoutSettings=True,
        )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert len(response["ReplicationTasks"]) == 1

        replication_task_arn = response["ReplicationTasks"][0]["ReplicationTaskArn"]

        if response["ReplicationTasks"][0]["Status"] == "running":
            start = datetime.now(shanghai_tz)

            response = client.stop_replication_task(
                ReplicationTaskArn=replication_task_arn,
            )

            assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

            wait_task_stop(client, task_identifier)

            stop_elapsed = datetime.now(shanghai_tz) - start
            stop_elapsed = datetime.fromtimestamp(stop_elapsed.total_seconds()).strftime("%M:%S")

            message = f"{task_identifier}, running -> stopped, {stop_elapsed}"
            send_message(message)

            print(datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S"), message)

        start = datetime.now(shanghai_tz)

        client.move_replication_task(
            ReplicationTaskArn=replication_task_arn,
            TargetReplicationInstanceArn=target_replication_instance_arn,
        )

        wait_task_stop(client, task_identifier)

        response = client.describe_replication_tasks(
            Filters=[
                {
                    "Name": "replication-task-id",
                    "Values": [
                        task_identifier,
                    ],
                },
            ],
            WithoutSettings=True,
        )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
        assert len(response["ReplicationTasks"]) == 1

        status = response["ReplicationTasks"][0]["Status"]

        move_elapsed = datetime.now(shanghai_tz) - start
        move_elapsed = datetime.fromtimestamp(move_elapsed.total_seconds()).strftime("%M:%S")

        message = f"{task_identifier}, moving -> {status}, {move_elapsed}"
        if status == "failed-move":
            message = f'{task_identifier}, <font color="warning">moving -> {status}</font>, {move_elapsed}'
        send_message(message)

        print(datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S"), message)

        start = datetime.now(shanghai_tz)

        client.start_replication_task(
            ReplicationTaskArn=replication_task_arn,
            StartReplicationTaskType="resume-processing",
        )

        wait_task_running(client, task_identifier)

        run_elapsed = datetime.now(shanghai_tz) - start
        run_elapsed = datetime.fromtimestamp(run_elapsed.total_seconds()).strftime("%M:%S")

        message = f"{task_identifier}, {status} -> running, {run_elapsed}"
        send_message(message)

        print(datetime.now(shanghai_tz).strftime("%Y-%m-%d %H:%M:%S"), message)
    except Exception as e:
        message = f"{task_identifier}, error: {e}"
        send_message(message)


def wait_task_stop(client, task_identifier):
    while True:
        response = client.describe_replication_tasks(
            Filters=[
                {
                    "Name": "replication-task-id",
                    "Values": [
                        task_identifier,
                    ],
                },
            ],
            WithoutSettings=True,
        )

        if response["ReplicationTasks"][0]["Status"] in ("stopped", "failed-move"):
            break

        time.sleep(10)


def wait_task_running(client, task_identifier):
    client.get_waiter("replication_task_running").wait(
        Filters=[
            {
                "Name": "replication-task-id",
                "Values": [
                    task_identifier,
                ],
            },
        ],
        WithoutSettings=True,
        WaiterConfig={
            "Delay": 10,
            "MaxAttempts": 18,
        },
    )


def send_message(message):
    data = {
        "msgtype": "markdown",
        "markdown": {
            "content": message,
        },
    }

    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=e9cb1d5b-9fc2-4d2e-8a92-35b500f565c8"

    requests.post(url=url, json=data)


def main():
    target_replication_instance_arn = os.getenv("TARGET_REPLICATION_INSTANCE_ARN")
    task_ids = sys.argv[1:]

    threads = []
    for task_id in task_ids:
        thread = threading.Thread(target=process_task, args=(task_id, target_replication_instance_arn))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
