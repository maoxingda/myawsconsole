import json
import re

import boto3
import botocore.exceptions
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.db import transaction

from dms.models import Task, Endpoint, Table, ReplicationTask, ReplicationEndpoint
from utils.http import HttpResponseRedirectToReferrer


def refresh_tasks(request):
    tasks = []
    client = boto3.client('dms')
    table_name = request.POST.get('table_name', '')
    endpoint_id = request.GET.get('endpoint_id', '')
    endpoint_arn = ''
    del_tasks = []
    for task in Task.objects.all():
        if settings.REPLICATION_TASK_SUFFIX not in task.name:
            del_tasks.append(task)
    for task in del_tasks:
        task.delete()
    if endpoint_id:
        try:
            endpoint = Endpoint.objects.get(id=endpoint_id)
            endpoint_arn = endpoint.arn
            res = client.describe_replication_tasks(Filters=[{'Name': 'endpoint-arn', 'Values': [endpoint_arn]}])
            for task in res['ReplicationTasks']:
                if not Task.objects.filter(name=task['ReplicationTaskIdentifier']).exists():
                    tasks.append(Task(
                        name=task['ReplicationTaskIdentifier'],
                        arn=task['ReplicationTaskArn'],
                        source_endpoint_arn=task['SourceEndpointArn'],
                        url=f"{settings.AWS_DMS_URL}#taskDetails/{task['ReplicationTaskIdentifier']}",
                        table_mappings=task['TableMappings']
                    ))
        except Endpoint.DoesNotExist as error:
            print(error)
        except botocore.exceptions.ClientError as error:
            print(error)
    else:
        paginator = client.get_paginator('describe_replication_tasks')
        for page in paginator.paginate():
            for task in page['ReplicationTasks']:
                dts_paginator = client.get_paginator('describe_table_statistics')
                for ts_page in dts_paginator.paginate(ReplicationTaskArn=task['ReplicationTaskArn']):
                    find = False
                    for stat in ts_page['TableStatistics']:
                        if table_name in stat['TableName']:
                            if not Task.objects.filter(name=task['ReplicationTaskIdentifier']).exists():
                                tasks.append(Task(
                                    name=task['ReplicationTaskIdentifier'],
                                    arn=task['ReplicationTaskArn'],
                                    source_endpoint_arn=task['SourceEndpointArn'],
                                    url=f"{settings.AWS_DMS_URL}#taskDetails/{task['ReplicationTaskIdentifier']}",
                                    table_mappings=task['TableMappings'],
                                    table_name=table_name
                                ))
                            find = True
                            break
                    if find:
                        break

    if tasks:
        Task.objects.bulk_create(tasks)

    return redirect(reverse(f'admin:{"_".join(request.path.split("/")[1:3])}_changelist') + f'?q={endpoint_arn}{table_name}')


def refresh_endpoints(request):
    endpoints = []
    remote_endpoint_identifiers = set()
    client = boto3.client('dms')
    server_name = request.POST.get('server_name', request.GET.get('server_name'))
    paginator = client.get_paginator('describe_endpoints')
    for page in paginator.paginate(Filters=[{'Name': 'engine-name', 'Values': ['mysql', 'mariadb', 'aurora', 'postgres', 'aurora-postgresql']}]):
        for endpoint in page['Endpoints']:
            if server_name == endpoint.get('ServerName'):
                remote_endpoint_identifiers.add(endpoint['EndpointIdentifier'])
                if not Endpoint.objects.filter(identifier=endpoint['EndpointIdentifier']).exists():
                    endpoints.append(Endpoint(
                        identifier=endpoint['EndpointIdentifier'],
                        arn=endpoint['EndpointArn'],
                        database=endpoint.get('DatabaseName'),
                        url=f'{settings.AWS_DMS_URL}#endpointDetails/{endpoint["EndpointIdentifier"]}',
                        server_name=server_name
                    ))

    local_endpoint_identifiers = {
        endpoint.identifier
        for endpoint in Endpoint.objects.filter(server_name=server_name)
    }
    del_endpoint_identifiers = local_endpoint_identifiers - remote_endpoint_identifiers
    Endpoint.objects.filter(identifier__in=del_endpoint_identifiers).delete()

    Endpoint.objects.bulk_create(endpoints)

    return redirect(reverse(f'admin:{"_".join(request.path.split("/")[1:3])}_changelist') + f'?q={server_name}')


def refresh_tables(request, task_id):
    task = Task.objects.get(id=task_id)
    client = boto3.client('dms')
    paginator = client.get_paginator('describe_table_statistics')
    tables = set()
    partition_table_name_suffix_pattern = re.compile(r'_p?\d+\w*$')
    for page in paginator.paginate(ReplicationTaskArn=task.arn):
        for stat in page['TableStatistics']:
            tables.add((partition_table_name_suffix_pattern.sub('', stat['TableName']), stat['SchemaName']))

    tables = [
        Table(name=table[0], schema=table[1], task_name=task.name, task=task) for table in tables
        if not Table.objects.filter(task_name=task.name, name=table[0]).exists()
    ]

    if tables:
        Table.objects.bulk_create(tables)

    return redirect(reverse(f'admin:{"_".join(request.path.split("/")[1:3])}_changelist') + f'?q={task.name}')


def download_table_mapping(request, task_id):
    task = Task.objects.get(id=task_id)

    return JsonResponse({
        'name': task.name,
        'table_mappings': json.dumps(task.table_mappings, indent=2)
    })


def stop_then_resume_task(request, task_id):
    task = get_object_or_404(ReplicationTask, pk=task_id)
    client = boto3.client('dms', region_name='cn-northwest-1')
    response = client.describe_replication_tasks(
        Filters=[
            {
                'Name': 'replication-task-arn',
                'Values': [
                    task.replication_task_arn,
                ]
            },
        ],
        WithoutSettings=True,
    )
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200
    assert len(response['ReplicationTasks']) == 1
    status = response['ReplicationTasks'][0]['Status']
    if 'running' == status:
        print(f'stopping task: {task.replication_task_identifier}')
        client.stop_replication_task(
            ReplicationTaskArn=task.replication_task_arn,
        )
        client.get_waiter('replication_task_stopped').wait(
            Filters=[
                {
                    'Name': 'replication-task-arn',
                    'Values': [
                        task.replication_task_arn,
                    ]
                },
            ],
            WithoutSettings=True,
        )
        print(f'resuming task: {task.replication_task_identifier}')
        client.start_replication_task(
            ReplicationTaskArn=task.replication_task_arn,
            StartReplicationTaskType='resume-processing',
        )
        client.get_waiter('replication_task_running').wait(
            Filters=[
                {
                    'Name': 'replication-task-arn',
                    'Values': [
                        task.replication_task_arn,
                    ]
                },
            ],
            WithoutSettings=True,
        )
        messages.info(request, f'任务 {task.replication_task_identifier} 已停止并恢复成功')

    return HttpResponseRedirectToReferrer(request)


def full_refresh_tasks(request):
    client = boto3.client('dms', region_name='cn-northwest-1')

    endpoints_paginator = client.get_paginator('describe_endpoints')

    endpoints = []
    for endpoints_page in endpoints_paginator.paginate():
        for endpoint in endpoints_page['Endpoints']:
            endpoints.append(
                ReplicationEndpoint(
                    endpoint_arn=endpoint['EndpointArn'],
                    endpoint_identifier=endpoint['EndpointIdentifier'],
                    endpoint_type=endpoint['EndpointType'],
                    engine_name=endpoint['EngineName'],
                    database_name=endpoint.get('DatabaseName') or '',
                    server_name=endpoint.get('ServerName') or '',
                    engine_display_name=endpoint['EngineDisplayName'],
                    status=endpoint['Status'],
                )
            )

    ReplicationEndpoint.objects.all().delete()
    ReplicationEndpoint.objects.bulk_create(endpoints)

    tasks_paginator = client.get_paginator('describe_replication_tasks')

    stats = []
    tasks = []
    for tasks_page in tasks_paginator.paginate():
        for task in tasks_page['ReplicationTasks']:
            tasks.append(
                ReplicationTask(
                    migration_type=task['MigrationType'],
                    recovery_checkpoint=task['RecoveryCheckpoint'],
                    replication_instance_arn=task['ReplicationInstanceArn'],
                    replication_task_arn=task['ReplicationTaskArn'],
                    replication_task_creation_date=task['ReplicationTaskCreationDate'],
                    replication_task_identifier=task['ReplicationTaskIdentifier'],
                    replication_task_settings=json.loads(task['ReplicationTaskSettings']),
                    replication_task_start_date=task['ReplicationTaskStartDate'],
                    replication_task_stats=task['ReplicationTaskStats'],
                    source_endpoint=ReplicationEndpoint.objects.get(endpoint_arn=task['SourceEndpointArn']),
                    target_endpoint=ReplicationEndpoint.objects.get(endpoint_arn=task['TargetEndpointArn']),
                    status=task['Status'],
                    table_mappings=json.loads(task['TableMappings']),
                    aws_console_url=f"{settings.AWS_DMS_URL}#taskDetails/{task['ReplicationTaskIdentifier']}",
                )
            )

            stats_paginator = client.get_paginator('describe_table_statistics')
            for stats_page in stats_paginator.paginate(ReplicationTaskArn=task['ReplicationTaskArn']):
                for stat in stats_page['TableStatistics']:
                    stats.append({
                        'name': stat['TableName'],
                        'schema': stat['SchemaName'],
                        'task_name': task['ReplicationTaskIdentifier'],
                    })

    ReplicationTask.objects.all().delete()
    ReplicationTask.objects.bulk_create(tasks)

    tables = []
    for stat in stats:
        tables.append(Table(
            name=stat['name'],
            schema=stat['schema'],
            task_name=stat['task_name'],
            task=ReplicationTask.objects.get(replication_task_identifier=stat['task_name']),
        ))

    Table.objects.all().delete()
    Table.objects.bulk_create(tables)

    messages.info(request, '刷新列表成功')

    return HttpResponseRedirectToReferrer(request)


def task_tables(request, task_id):
    task = ReplicationTask.objects.get(id=task_id)

    return redirect(reverse('admin:dms_table_changelist') + f'?q={task.replication_task_identifier}')
