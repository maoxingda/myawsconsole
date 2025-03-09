import re
from collections import defaultdict
from operator import itemgetter

import boto3
import pandas
from django.core.management import BaseCommand
from tabulate import tabulate


class Command(BaseCommand):
    help = "统计DMS任务同步的表的统计数据"

    # 分区表正则表达式（复合分区、范围分区、哈希分区顺序不能调整）
    partition_table_name_patterns = [
        # 复合分区
        (
            re.compile(r"([_a-z0-9]+[a-z])_p?\d{1,3}_default"),
            "先哈希分区（1到3位数字）再范围分区（默认分区）",
        ),  # 分区前缀标识字母：p为可选的
        (
            re.compile(r"([_a-z0-9]+[a-z])_p?\d{1,3}_p?\d{4}"),
            "先哈希分区（1到3位数字）再范围分区（按年分区）",
        ),
        (
            re.compile(r"([_a-z0-9]+[a-z])_p?\d{1,3}_p?(?:\d{6}|\d{4}_\d{2})"),
            "先哈希分区（1到3位数字）再范围分区（按月分区）",
        ),
        (
            re.compile(r"([_a-z0-9]+[a-z])_p?\d{1,3}_p?(?:\d{8}|\d{4}_\d{2}_\d{2})"),
            "先哈希分区（1到3位数字）再范围分区（按日分区）",
        ),
        (
            re.compile(r"([_a-z0-9]+[a-z])_default_p?\d{1,3}"),
            "先范围分区（默认分区）再哈希分区（1到3位数字）",
        ),
        (
            re.compile(r"([_a-z0-9]+[a-z])_p?\d{4}_p?\d{1,3}"),
            "先范围分区（按年分区）再哈希分区（1到3位数字）",
        ),
        (
            re.compile(r"([_a-z0-9]+[a-z])_p?(?:\d{6}|\d{4}_\d{2})_p?\d{1,3}"),
            "先范围分区（按月分区）再哈希分区（1到3位数字）",
        ),
        (
            re.compile(r"([_a-z0-9]+[a-z])_p?(?:\d{8}|\d{4}_\d{2}_\d{2})_p?\d{1,3}"),
            "先范围分区（按日分区）再哈希分区（1到3位数字）",
        ),
        # 范围分区
        (re.compile(r"([_a-z0-9]+[a-z])_default"), "范围分区（默认分区）"),
        (re.compile(r"([_a-z0-9]+[a-z])_p?\d{4}"), "范围分区（按年分区）"),
        (
            re.compile(r"([_a-z0-9]+[a-z])_p?(?:\d{6}|\d{4}_\d{2})"),
            "范围分区（按月分区）",
        ),
        (
            re.compile(r"([_a-z0-9]+[a-z])_p?(?:\d{8}|\d{4}_\d{2}_\d{2})"),
            "范围分区（按日分区）",
        ),
        # 哈希分区
        (re.compile(r"([_a-z0-9]+[a-z])_p?\d{1,3}"), "哈希分区（1到3位数字）"),
    ]

    def handle(self, *args, **options):
        client = boto3.client("dms")
        drt_paginator = client.get_paginator("describe_replication_tasks")
        tasks = []
        table_stats = defaultdict(list)
        i = 0
        for drt_page in drt_paginator.paginate(
            Filters=[
                {
                    "Name": "endpoint-arn",
                    "Values": [
                        "arn:aws-cn:dms:cn-northwest-1:321659100662:endpoint:VRZIQ343VLKKRNM3D4LE2KMCKLZVN6CJVR7BGMQ",
                        "arn:aws-cn:dms:cn-northwest-1:321659100662:endpoint:B24F5G5SNPNDNLL55O4QWJTLPJ64ECOYARRLVCQ",
                    ],
                }
            ],
            WithoutSettings=True,
        ):
            for task in drt_page["ReplicationTasks"]:
                tasks.append(task["ReplicationTaskIdentifier"])
                endpoint = client.describe_endpoints(
                    Filters=[
                        {
                            "Name": "endpoint-arn",
                            "Values": [task["SourceEndpointArn"]],
                        }
                    ]
                )["Endpoints"][0]
                database_name = endpoint.get("DatabaseName", "")
                if database_name:
                    database_name += "."
                dts_paginator = client.get_paginator("describe_table_statistics")
                for dts_page in dts_paginator.paginate(
                    ReplicationTaskArn=task["ReplicationTaskArn"]
                ):
                    # if i > 100:
                    #     break
                    for stat in dts_page["TableStatistics"]:
                        i += 1
                        table_name = f"{stat['SchemaName']}.{stat['TableName']}"
                        for pattern, _ in self.partition_table_name_patterns:
                            match = pattern.fullmatch(stat["TableName"])
                            if match:
                                # sys.stderr.write(f"{table_name}\n")
                                table_name = f"{stat['SchemaName']}.{match.group(1)}"
                                break
                        cdc_counts = stat["Inserts"] + stat["Updates"] + stat["Deletes"]
                        if cdc_counts > 0:
                            table_stats[f"{database_name}{table_name}"].append(
                                [
                                    cdc_counts,
                                    task["ReplicationTaskIdentifier"],
                                    task["ReplicationTaskStartDate"].replace(
                                        tzinfo=None
                                    ),
                                ]
                            )
                            # print(f"{table_name:<64}", cdc_counts, task["ReplicationTaskIdentifier"])

        table_stats = [
            [
                table_name,
                sum(cnt for cnt, *_ in val),
                val[0][2],
                f"https://cn-northwest-1.console.amazonaws.cn/dms/v2/home"
                f"?region=cn-northwest-1#taskDetails/{val[0][1]}",
            ]
            for table_name, val in table_stats.items()
        ]
        table_stats.sort(key=itemgetter(1), reverse=True)
        print(tabulate(table_stats[:20], showindex="always", tablefmt="simple_grid"))
        # print(i)
        # pprint(sorted(tasks))

        df = pandas.DataFrame(
            table_stats, columns=["table_name", "cdc_counts", "start_date", "task"]
        )
        df.to_excel("table-stats.xlsx", index=False)
