import os
import re
import time
from datetime import datetime, timedelta

import boto3
import psycopg2
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from redshift.models import Snapshot, Table, RestoreTableTask, RestoreClusterTask, Cluster
from redshift.util.corp_wechat import send_message


def refresh_clusters(request):
    clusters = []
    client = boto3.client('redshift')
    paginator = client.get_paginator('describe_clusters')
    restore_cluster_pattern = re.compile(r'snapshot-\d{8}t\d{6}$')
    for page in paginator.paginate():
        for cluster in page['Clusters']:
            if restore_cluster_pattern.search(cluster['ClusterIdentifier']) and cluster['ClusterStatus'] == 'available':
                if not Cluster.objects.filter(identifier=cluster['ClusterIdentifier']).exists():
                    clusters.append(Cluster(identifier=cluster['ClusterIdentifier']))

    if clusters:
        Cluster.objects.bulk_create(clusters)

    return redirect(reverse(f'admin:{"_".join(request.path.split("/")[1:3])}_changelist'))


def refresh_snapshots(request):
    snapshots = []
    client = boto3.client('redshift')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    if start_date:
        start_time = datetime.strptime(start_date, '%Y/%m/%d') - timedelta(hours=8)
    else:
        # redshift集群快照最多只能保存35天
        start_time = datetime.utcnow() - timedelta(days=35)
    if end_date:
        end_time = datetime.strptime(end_date, '%Y/%m/%d') + timedelta(hours=16)
    else:
        end_time = datetime.utcnow()
    paginator = client.get_paginator('describe_cluster_snapshots')
    snapshot_identifier_pattern = re.compile(r'\d\d\d\d-\d\d-\d\d-\d\d-\d\d-\d\d$')
    for page in paginator.paginate(StartTime=start_time, EndTime=end_time):
        for snapshot in page['Snapshots']:
            if not snapshot_identifier_pattern.search(snapshot['SnapshotIdentifier']):
                continue
            if Snapshot.objects.filter(cluster=snapshot['ClusterIdentifier'], identifier=snapshot['SnapshotIdentifier']).exists():
                continue
            snapshots.append(
                Snapshot(
                    create_time=snapshot['SnapshotCreateTime'],
                    create_time_str=(snapshot['SnapshotCreateTime'] + timedelta(hours=8)).strftime('%Y%m%d%H%M'),
                    cluster=snapshot['ClusterIdentifier'],
                    identifier=snapshot['SnapshotIdentifier']
                )
            )

    if snapshots:
        Snapshot.objects.bulk_create(snapshots)

    return redirect(reverse(f'admin:{"_".join(request.path.split("/")[1:3])}_changelist'))


def refresh_tables(request):
    dns = os.getenv('dns')

    tables = []
    suffix_filter = re.compile(r'(?:_stg|_staging|_tmp|_temp|_tmp\d+|_temp\d+|_increment)$')
    with psycopg2.connect(dns) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                select database_name || '.' || schema_name || '.' || table_name, schema_name from svv_redshift_tables
                where table_type = 'TABLE' and schema_name in ('ods', 'stg', 'dim', 'dwd', 'dws', 'met', 'ads')
            """)
            for row in cursor.fetchall():
                table_name = row[0]
                schema = row[1]
                if not suffix_filter.search(table_name) and not Table.objects.filter(name=table_name).exists():
                    tables.append(Table(name=table_name, schema=schema))

    if tables:
        Table.objects.bulk_create(tables)

    return redirect(reverse(f'admin:{"_".join(request.path.split("/")[1:3])}_changelist'))


def launch_restore_table_task(request, task_id):
    task = RestoreTableTask.objects.get(id=task_id)
    task.status = RestoreTableTask.StatusEnum.RUNNING.name
    task.save()
    try:
        client = boto3.client('redshift')
        dns = os.getenv('dns')
        conn = psycopg2.connect(dns)
        cursor = conn.cursor()
        for table in task.tables.all():
            target_table_name = table.name.split(".")[
                                    2] + f'_{(task.snapshot.create_time + timedelta(hours=8)).strftime("%Y%m%d%H%M")}'
            cursor.execute(f"""
                select 1 from svv_redshift_tables where schema_name = 'temp' and table_name = '{target_table_name}'
            """)
            if cursor.fetchall():
                print(f'目标表：temp.{target_table_name} 已经存在，跳过...')
                continue

            start = datetime.now()
            # 集群在连续两次恢复快照操作之间必须等待集群状态更新为：Available
            while True:
                response = client.describe_clusters(ClusterIdentifier=task.snapshot.cluster)

                cluster_status = response['Clusters'][0]['ClusterAvailabilityStatus']

                print(f'cluster status: {cluster_status}, elapsed: {int((datetime.now() - start).total_seconds())} 秒')

                if cluster_status == 'Available':
                    break

                time.sleep(15)

            response = client.restore_table_from_cluster_snapshot(
                ClusterIdentifier=task.snapshot.cluster,
                SnapshotIdentifier=task.snapshot.identifier,
                SourceDatabaseName=table.name.split('.')[0],
                SourceSchemaName=table.name.split('.')[1],
                SourceTableName=table.name.split('.')[2],
                TargetDatabaseName=table.name.split('.')[0],
                TargetSchemaName='temp',
                NewTableName=target_table_name,
            )
            req_id = response['TableRestoreStatus']['TableRestoreRequestId']

            start = datetime.now()
            while (datetime.now() - start).total_seconds() / 60 < 15:
                response = client.describe_table_restore_status(
                    ClusterIdentifier=task.snapshot.cluster,
                    TableRestoreRequestId=req_id,
                )

                status = response['TableRestoreStatusDetails'][0]['Status']

                print(f'temp.{target_table_name}, {status}, elapsed: {int((datetime.now() - start).total_seconds())} 秒')

                if status in ['SUCCEEDED', 'FAILED', 'CANCELED']:
                    break

                time.sleep(15)

        if task.is_nofity:
            send_message(f'###### 任务：<font color="info">{task.name}</font> 完成')

        task.status = RestoreTableTask.StatusEnum.COMPLETED.name
        task.save()
    except:
        task.status = RestoreTableTask.StatusEnum.CREATED.name
        task.save()

    return HttpResponse('恢复表任务成功')


def launch_restore_cluster_task(request, task_id):
    client = boto3.client('redshift')
    task = RestoreClusterTask.objects.get(id=task_id)
    task.status = RestoreClusterTask.StatusEnum.RUNNING.name
    task.save()
    try:
        cluster_id = task.snapshot.cluster
        snapshot_id = task.snapshot.identifier
        local_datetime_from_snapshot_id = (
                    datetime.strptime(snapshot_id[-19:], "%Y-%m-%d-%H-%M-%S") + timedelta(hours=8)).strftime(
            '%Y%m%dT%H%M%S')
        restore_cluster_id = f'{cluster_id}-snapshot-{local_datetime_from_snapshot_id}'

        cluster_addr = f'{settings.AWS_REDSHIFT_URL}#cluster-details?cluster={restore_cluster_id.lower()}'
        snapshot_url = reverse("admin:redshift_snapshot_change", kwargs={'object_id': task.snapshot.id})

        is_find = False
        paginator = client.get_paginator('describe_clusters')
        for page in paginator.paginate():
            for cluster in page['Clusters']:
                if cluster['ClusterIdentifier'] == restore_cluster_id.lower():
                    is_find = True

        if is_find:
            send_message(f'###### 集群：[{restore_cluster_id.lower()}]({cluster_addr}) 已经存在')
        else:
            response = client.describe_clusters(ClusterIdentifier=cluster_id)

            client.restore_from_cluster_snapshot(
                ClusterIdentifier=restore_cluster_id,
                SnapshotIdentifier=snapshot_id,
                SnapshotClusterIdentifier=cluster_id,
                ClusterSubnetGroupName=response['Clusters'][0]['ClusterSubnetGroupName'],
                ClusterParameterGroupName=response['Clusters'][0]['ClusterParameterGroups'][0]['ParameterGroupName'],
                VpcSecurityGroupIds=[response['Clusters'][0]['VpcSecurityGroups'][0]['VpcSecurityGroupId']],
            )

            start = datetime.now()
            # 等待集群状态更新为：Available
            while True:
                response = client.describe_clusters(ClusterIdentifier=restore_cluster_id)

                cluster_status = response['Clusters'][0]['ClusterStatus']

                print(f'cluster status: {cluster_status}, elapsed: {int((datetime.now() - start).total_seconds())} 秒')

                if cluster_status == 'available':
                    break

                time.sleep(15)

            send_message(
                f'###### 从快照 [{snapshot_id}]({settings.MY_AWS_URL}{snapshot_url}) 创建集群 [{restore_cluster_id.lower()}]({cluster_addr}) 成功')

        task.status = RestoreClusterTask.StatusEnum.COMPELETED.name
        task.save()
    except:
        task.status = RestoreClusterTask.StatusEnum.CREATED.name
        task.save()

    return HttpResponse('恢复集群成功')


def download_sql(request, task_id):
    task = RestoreTableTask.objects.get(id=task_id)
    sqls = []
    for table in task.tables.all():
        target_table_name = table.name.split(".")[
                                2] + f'_{(task.snapshot.create_time + timedelta(hours=8)).strftime("%Y%m%d%H%M")}'
        sqls.append(f'select * from temp.{target_table_name} limit 1;')
    return JsonResponse({'sql': sqls, 'name': task.name})


def batch_download_sql(request):
    task_ids = request.GET.get('task_ids', '').split(',')
    task_ids = [int(task_id) for task_id in task_ids[:-1]]
    tasks = RestoreTableTask.objects.in_bulk(task_ids).values()
    sqls = ''
    for task in tasks:
        for table in task.tables.all():
            target_table_name = table.name.split(".")[
                                    2] + f'_{(task.snapshot.create_time + timedelta(hours=8)).strftime("%Y%m%d%H%M")}'
            sqls += f'select * from temp.{target_table_name} limit 1;\n'
    return JsonResponse({'sqls': sqls, 'name': task.name})
