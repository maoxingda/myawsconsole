import json
import os
import re
import time
from datetime import datetime

import boto3
import mysql.connector
import psycopg2
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.safestring import mark_safe

from schemagenerator.models import DbConn, Table, Task


def db_tables(request, conn_id):
    db_conn = DbConn.objects.get(id=conn_id)
    partition_table_name_suffix_pattern = re.compile(r'_\d+\w*$')
    pg_prefix_pattern = re.compile(r'^pg_')
    if db_conn.db_type == DbConn.DbType.POSTGRESQL.value:
        with psycopg2.connect(db_conn.server_address()) as conn:
            with conn.cursor() as cursor:
                query = f"select table_name from information_schema.tables where table_type = 'BASE TABLE'"
                query = f"select tablename from pg_catalog.pg_tables"
                cursor.execute(query)

                results = cursor.fetchall()

                tables = set()
                for row in results:
                    table_name = row[0]
                    if not Table.objects.filter(conn=db_conn, name=table_name).exists():
                        if not Table.objects.filter(conn=db_conn, name=table_name).exists() and \
                                not pg_prefix_pattern.search(table_name):
                            tables.add(partition_table_name_suffix_pattern.sub('', table_name))

                if tables:
                    tables = [Table(name=table_name, conn=db_conn) for table_name in tables]
                    Table.objects.bulk_create(tables)
    elif db_conn.db_type == DbConn.DbType.MYSQL.value:
        config = {
            'user': db_conn.user,
            'password': db_conn.password,
            'host': db_conn.dns,
            'port': db_conn.port,
            'database': db_conn.name,
        }
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        query = f"select table_name from information_schema.tables where table_schema = '{db_conn.name}' and table_type = 'BASE TABLE'"
        cursor.execute(query)

        results = cursor.fetchall()

        tables = []
        for row in results:
            table_name = row[0]
            if not Table.objects.filter(conn=db_conn, name=table_name).exists():
                tables.append(Table(name=table_name, conn=db_conn))

        if tables:
            Table.objects.bulk_create(tables)

        cursor.close()
        conn.close()

    return redirect(reverse(f'admin:{"_".join(request.path.split("/")[1:3])}_changelist'))


def launch_task(request, task_id):
    task = Task.objects.get(id=task_id)
    task.status = Task.StatusEnum.RUNNING.name
    task.save()
    try:
        client = boto3.client('dms')
        endpoint_id = f'{task.conn.name.replace("_", "-")}-sync-schema-source'
        is_find = False
        source_endpoint_arn = ''
        paginator = client.get_paginator('describe_endpoints')
        for page in paginator.paginate(Filters=[{'Name': 'endpoint-type', 'Values': ['source']}]):
            for endpoint in page['Endpoints']:
                if endpoint_id == endpoint['EndpointIdentifier']:
                    is_find = True
                    source_endpoint_arn = endpoint['EndpointArn']
        if not is_find:
            config = {
                'EndpointIdentifier': endpoint_id,
                'EndpointType': 'source',
                'EngineName': task.conn.db_type,
                'Username': task.conn.user,
                'Password': task.conn.password,
                'Port': task.conn.port,
                'ServerName': task.conn.dns,
                'SslMode': 'none',
            }
            if task.conn.db_type == DbConn.DbType.POSTGRESQL.value:
                config['DatabaseName'] = task.conn.name
            client.create_endpoint(**config)

            start = datetime.now()
            while True:
                response = client.describe_endpoints(
                    Filters=[
                        {
                            'Name': 'endpoint-id',
                            'Values': [
                                endpoint_id
                            ]
                        }
                    ]
                )

                status = response['Endpoints'][0]['Status']

                elapsed = datetime.now() - start

                print(f'endpoint: {endpoint_id}, status: {status}, elapsed: {int(elapsed.seconds)} 秒')

                if status == 'active':
                    source_endpoint_arn = response['Endpoints'][0]['EndpointArn']
                    break

                time.sleep(15)

        table_mappings = {
            'rules': [
                {
                    'rule-type': 'transformation',
                    'rule-id': 1,
                    'rule-name': 1,
                    'rule-target': 'table',
                    'object-locator': {
                        'schema-name': '%',
                        'table-name': '%'
                    },
                    'rule-action': 'add-prefix',
                    'value': task.conn.target_table_name_prefix,
                    'old-value': None
                },
                {
                    'rule-type': 'transformation',
                    'rule-id': 2,
                    'rule-name': 2,
                    'rule-target': 'schema',
                    'object-locator': {
                        'schema-name': '%'
                    },
                    'rule-action': 'rename',
                    'value': task.conn.target_schema,
                    'old-value': None
                }
            ]
        }
        schema_name = task.conn.name if task.conn.db_type == DbConn.DbType.MYSQL.value else task.conn.schema
        for i, task_table in enumerate(task.sync_tables.all()):
            table_mappings['rules'].append({
                'rule-id': 10001 + i,
                'rule-name': 10001 + i,
                'rule-type': 'selection',
                'object-locator': {
                    'schema-name': schema_name,
                    'table-name': task_table.table.name
                },
                'rule-action': 'include',
                'filters': [
                    {
                        'filter-type': 'source',
                        'column-name': 'id',
                        'filter-conditions': [
                            {
                                'filter-operator': 'null'
                            }
                        ]
                    }
                ]
            })

        if os.getlogin() == 'root':
            response = client.describe_endpoints(
                Filters=[
                    {
                        'Name': 'endpoint-id',
                        'Values': [
                            'bi-sandbox-acceptanydate'
                        ]
                    }
                ]
            )
            target_endpoint_arn = response['Endpoints'][0]['EndpointArn']
            response = client.describe_replication_instances(
                Filters=[
                    {
                        'Name': 'replication-instance-id',
                        'Values': [
                            'bi-sandbox-private-replication-instance'
                        ]
                    }
                ]
            )
            replication_instance_arn = response['ReplicationInstances'][0]['ReplicationInstanceArn']
        else:
            response = client.describe_endpoints(
                Filters=[
                    {
                        'Name': 'endpoint-id',
                        'Values': [
                            'bi-prod-hc'
                        ]
                    }
                ]
            )
            target_endpoint_arn = response['Endpoints'][0]['EndpointArn']
            response = client.describe_replication_instances(
                Filters=[
                    {
                        'Name': 'replication-instance-id',
                        'Values': [
                            'hc-replica-server-private'
                        ]
                    }
                ]
            )
            replication_instance_arn = response['ReplicationInstances'][0]['ReplicationInstanceArn']

        is_find = False
        replication_task_arn = ''
        replication_task_id = f'{endpoint_id}-to-redshift-onlyonce'
        paginator = client.get_paginator('describe_replication_tasks')
        for page in paginator.paginate(Filters=[{'Name': 'migration-type', 'Values': ['full-load']}]):
            for replication_task in page['ReplicationTasks']:
                if replication_task['ReplicationTaskIdentifier'] == replication_task_id:
                    is_find = True
                    replication_task_arn = replication_task['ReplicationTaskArn']
        if not is_find:
            response = client.create_replication_task(
                ReplicationTaskIdentifier=replication_task_id,
                MigrationType='full-load',
                ReplicationInstanceArn=replication_instance_arn,
                SourceEndpointArn=source_endpoint_arn,
                TargetEndpointArn=target_endpoint_arn,
                TableMappings=json.dumps(table_mappings),
            )
            replication_task_arn = response['ReplicationTask']['ReplicationTaskArn']

        start = datetime.now()
        while True:
            response = client.describe_replication_tasks(Filters=[{'Name': 'replication-task-id', 'Values': [replication_task_id]}])

            status = response['ReplicationTasks'][0]['Status']

            elapsed = datetime.now() - start

            print(f'task: {replication_task_id}, status: {status}, elapsed: {int(elapsed.seconds)} 秒')

            if status == 'ready':
                break

            time.sleep(10)

        client.start_replication_task(
            ReplicationTaskArn=replication_task_arn,
            StartReplicationTaskType='start-replication',
        )

        start = datetime.now()
        while True:
            response = client.describe_replication_tasks(Filters=[{'Name': 'replication-task-id', 'Values': [replication_task_id]}])

            status = response['ReplicationTasks'][0]['Status']

            elapsed = datetime.now() - start

            print(f'task: {replication_task_id}, status: {status}, elapsed: {int(elapsed.seconds)} 秒')

            if status == 'stopped':
                break

            time.sleep(10)

        task.status = Task.StatusEnum.COMPLETED.name
        task.save()
    except:
        task.status = Task.StatusEnum.COMPLETED.CREATED.name
        task.save()

    return HttpResponse()


def download_sql(request, task_id):
    task = Task.objects.get(id=task_id)
    sql = ''
    for task_table in task.sync_tables.all():
        sql += f'select * from {task.conn.target_schema}.{task.conn.target_table_name_prefix}{task_table.table.name};\n'

    return JsonResponse({'name': task.name, 'sql': sql})


def create_ddl_sql(request, task_id):
    req_schema = request.GET.get('schema')
    task = get_object_or_404(Task, id=task_id)
    dns = os.getenv('dns')
    with psycopg2.connect(dns) as conn:
        with conn.cursor() as cursor:
            ddl_sql = ''
            for sync_table in task.sync_tables.all():
                query_columns_sql = f"select column_name, data_type, character_maximum_length, numeric_precision, numeric_scale " \
                                    f"from pg_catalog.svv_all_columns where schema_name = '{task.conn.target_schema}' and " \
                                    f"table_name = '{task.conn.target_table_name_prefix}{sync_table.table.name}'"
                print(query_columns_sql)
                cursor.execute(query_columns_sql)
                columns = cursor.fetchall()
                max_column_lengh = max([len(column) + 2 for column, *rest in columns] + [1])
                max_column_lengh = 25 if max_column_lengh < 25 else max_column_lengh

                external = ''
                if_not_exists = ''
                if req_schema == 'emr':
                    external = 'external '
                else:
                    if_not_exists = 'if not exists '

                # ddl_sql += f'drop table if exists {req_schema}.{"db_" if req_schema == "ods" else ""}{table_name_prefix}_{table.name};\n'

                ddl_sql += f'create {external}table {if_not_exists}{req_schema}.{"db_" if req_schema == "ods" else ""}{task.conn.target_table_name_prefix}{sync_table.table.name}\n' \
                           f'(\n'
                for column, data_type, column_lengh, numeric_precision, numeric_scale in columns:
                    column = f'"{column}"'
                    if data_type in ('smallint', 'integer', 'bigint', 'date', 'timestamp', 'real', 'double precision'):
                        ddl_sql += f'    {column.ljust(max_column_lengh)} {data_type},\n'
                    elif data_type in ('timestamp without time zone',):
                        ddl_sql += f'    {column.ljust(max_column_lengh)} timestamp,\n'
                    elif data_type in ('numeric',):
                        ddl_sql += f'    {column.ljust(max_column_lengh)} {data_type}({numeric_precision}, {numeric_scale}),\n'
                    elif data_type in ('string', 'character varying'):
                        if column == 'op':
                            ddl_sql += f'    {column.ljust(max_column_lengh)} char(1),\n'
                        else:
                            ddl_sql += f'    {column.ljust(max_column_lengh)} varchar({column_lengh}),\n'
                    else:
                        messages.error(request, mark_safe(f'<pre>未知数据类型：{task.conn.target_schema, sync_table.table.name, column, data_type}</pre>'))

                ddl_sql += f"    {'commit_timestamp'.ljust(max_column_lengh)} varchar(50),\n"
                ddl_sql += f"    {'op'.ljust(max_column_lengh)} char(1),\n"
                ddl_sql += f"    {'cdc_transact_id'.ljust(max_column_lengh)} varchar(50),\n"
                if req_schema == 'ods':
                    ddl_sql += f"    {'event_time'.ljust(max_column_lengh)} varchar(128),\n"
                    ddl_sql += f"    {'timestamp_executed_insert'.ljust(max_column_lengh)} timestamp default sysdate + interval '8h',\n"
                    ddl_sql += f"    {'timestamp_executed_update'.ljust(max_column_lengh)} timestamp default sysdate + interval '8h'\n"
                else:
                    ddl_sql = ddl_sql[:-2] + '\n'
                ddl_sql += ')\n'
                if req_schema == 'emr':
                    ddl_sql += 'partitioned by (event_time varchar(128))\n'
                    ddl_sql += 'stored as parquet\n'
                    ddl_sql += f"location '{task.conn.s3_path}'\n"
                ddl_sql += f";\n\n"

    return JsonResponse({
        'schema': req_schema,
        'ddl_sql': ddl_sql
    })