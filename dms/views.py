import json
import re

import boto3
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from dms.models import Task, Endpoint, Table


def refresh_tasks(request):
    tasks = []
    client = boto3.client('dms')
    table_name = request.POST.get('table_name', '')
    endpoint_id = request.GET.get('endpoint_id')
    endpoint_arn = ''
    paginator = client.get_paginator('describe_replication_tasks')
    for page in paginator.paginate():
        for task in page['ReplicationTasks']:
            if endpoint_id:
                endpoint = Endpoint.objects.get(id=endpoint_id)
                endpoint_arn = endpoint.arn
                if endpoint.arn in (task['SourceEndpointArn'], task['TargetEndpointArn']):
                    if not Task.objects.filter(name=task['ReplicationTaskIdentifier']).exists():
                        tasks.append(Task(
                            name=task['ReplicationTaskIdentifier'],
                            arn=task['ReplicationTaskArn'],
                            source_endpoint_arn=task['SourceEndpointArn'],
                            url=f"{settings.AWS_DMS_URL}#taskDetails/{task['ReplicationTaskIdentifier']}",
                            table_mappings=task['TableMappings']
                        ))
                continue

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
    client = boto3.client('dms')
    server_name = request.POST.get('server_name', request.GET.get('server_name'))
    paginator = client.get_paginator('describe_endpoints')
    for page in paginator.paginate():
        for endpoint in page['Endpoints']:
            if server_name == endpoint.get('ServerName'):
                if not Endpoint.objects.filter(identifier=endpoint['EndpointIdentifier']).exists():
                    endpoints.append(Endpoint(
                        identifier=endpoint['EndpointIdentifier'],
                        arn=endpoint['EndpointArn'],
                        database=endpoint['DatabaseName'] if endpoint.get('DatabaseName') else None,
                        url=f'{settings.AWS_DMS_URL}#endpointDetails/{endpoint["EndpointIdentifier"]}',
                        server_name=server_name
                    ))

    del_endpoints = []
    for endpoint in Endpoint.objects.filter(identifier__endswith='-sync-schema-source'):
        if not any([endpoint.identifier == ep.identifier for ep in endpoints]):
            del_endpoints.append(endpoint)
    for del_ep in del_endpoints:
        del_ep.delete()

    if endpoints:
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
        Table(name=table[0], schema=table[1], task_name=task.name) for table in tables
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
