import boto3
from django.shortcuts import redirect
from django.urls import reverse

from dms.models import Task, Endpoint


def refresh_tasks(request):
    tasks = []
    client = boto3.client('dms')
    table_name = request.GET.get('search_table')
    paginator = client.get_paginator('describe_replication_tasks')
    for page in paginator.paginate():
        for task in page['ReplicationTasks']:
            dts_paginator = client.get_paginator('describe_table_statistics')
            for ts_page in dts_paginator.paginate(ReplicationTaskArn=task['ReplicationTaskArn']):
                find = False
                for stat in ts_page['TableStatistics']:
                    if table_name in stat['TableName']:
                        tasks.append(Task(
                            name=task['ReplicationTaskIdentifier'],
                            url=f"https://cn-northwest-1.console.amazonaws.cn/dms/v2/home?"
                                f"region=cn-northwest-1#taskDetails/{task['ReplicationTaskIdentifier']}",
                            table_mappings=task['TableMappings']
                        ))
                        find = True
                        break
                if find:
                    break

    if tasks:
        Task.objects.all().delete()
        Task.objects.bulk_create(tasks)

    request.session['search_table'] = table_name

    return redirect(reverse('admin:dms_task_changelist'))


def refresh_endpoints(request):
    endpoints = []
    client = boto3.client('dms')
    server_name = request.GET.get('server_name')
    paginator = client.get_paginator('describe_endpoints')
    for page in paginator.paginate():
        for endpoint in page['Endpoints']:
            if server_name in endpoint.get('ServerName', []):
                endpoints.append(Endpoint(
                    identifier=endpoint['EndpointIdentifier'],
                    arn=endpoint['EndpointArn'],
                    database=endpoint['DatabaseName'] if endpoint.get('DatabaseName') else None,
                    url=f'https://cn-northwest-1.console.amazonaws.cn/dms/v2/home?' \
                        f'region=cn-northwest-1#endpointDetails/{endpoint["EndpointIdentifier"]}'
                ))

    if endpoints:
        Endpoint.objects.all().delete()
        Endpoint.objects.bulk_create(endpoints)

    request.session['server_name'] = server_name

    return redirect(reverse('admin:dms_endpoint_changelist'))