import boto3


def main():
    client = boto3.client('dms')

    # 获取所有任务
    task_paginator = client.get_paginator('describe_replication_tasks')

    task_table_counts = []
    for task_page in task_paginator.paginate():
        for task in task_page['ReplicationTasks']:
            table_count = 0
            task_id = task['ReplicationTaskIdentifier']

            stats_paginator = client.get_paginator('describe_table_statistics')

            for stats_page in stats_paginator.paginate(ReplicationTaskArn=task['ReplicationTaskArn']):
                table_count += len(stats_page['TableStatistics'])

            # 存储任务和其表数量
            task_table_counts.append((task_id, table_count))

    # 排序，获取最多同步表的前10个任务
    top_10_tasks = sorted(task_table_counts, key=lambda x: x[1], reverse=True)[:10]

    # 打印结果
    print("Top 10 tasks with the most tables synced:\n")
    for task_id, table_count in top_10_tasks:
        print(f"Task ID: {task_id:<80}, Tables Synced: {table_count}")


if __name__ == '__main__':
    main()
