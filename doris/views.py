import json
import os
import re
import textwrap
from enum import Enum
from pprint import pprint

import mysql.connector
import psycopg2
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from doris import models


class TargetDatabase(Enum):
    DORIS = 0
    REDSHIFT = 1


def execute_sql(sql: str, tgt_db: TargetDatabase = TargetDatabase.REDSHIFT, ret_val: bool = False):
    if tgt_db == TargetDatabase.REDSHIFT:
        dns = os.getenv('dns')
        with psycopg2.connect(dns) as conn:
            with conn.cursor() as cursor:
                print(sql)
                print('-' * 128)
                cursor.execute(sql)
                if ret_val:
                    return cursor.fetchall()
    elif tgt_db == TargetDatabase.DORIS:
        config = {
            'user'    : 'rdw',
            'password': os.getenv('password'),
            'host'    : '10.128.1.220',
            'port'    : '6033',
            'database': 'test',
        }
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=True)

        print(sql)
        print('-' * 128)
        cursor.execute(sql)

        if ret_val:
            return cursor.fetchall()

        cursor.close()
        conn.close()
    else:
        raise Exception(f'Unknown database type: {tgt_db!r}')


def start_s3_load_task(request, task_id):
    task: models.S3LoadTask = models.S3LoadTask.objects.select_related('table').get(id=task_id)
    table = task.table

    sql = textwrap.dedent(f"""
            select column_name, data_type, character_maximum_length, numeric_precision, numeric_scale 
            from svv_all_columns where schema_name = 'temp' and table_name = '{table.name}'
        """)
    columns = execute_sql(sql, ret_val=True)

    drop_table_ddl = f'drop table if exists test.{table.name}\n'
    create_table_ddl = f'create table test.{table.name}\n' \
                       f'(\n'
    for i, row in enumerate(columns):
        column_name, data_type, character_maximum_length, numeric_precision, numeric_scale = row
        if data_type == 'character varying':
            if column_name in re.split(r',\s*', task.sort_key):
                create_table_ddl += f'    {column_name} varchar({character_maximum_length})'
            else:
                create_table_ddl += f'    {column_name} string'
        elif data_type == 'timestamp without time zone':
            create_table_ddl += f'    {column_name} datetime'
        else:
            create_table_ddl += f'    {column_name} {data_type}'
        if i + 1 < len(columns):
            create_table_ddl += ','
        create_table_ddl += '\n'
    create_table_ddl += ')\n'

    if task.type == models.S3LoadTask.TableType.DETAIL:
        create_table_ddl += f'duplicate key({task.sort_key})\n'
    elif task.type == models.S3LoadTask.TableType.AGG:
        create_table_ddl += f'aggregate key({task.sort_key})\n'
    elif task.type == models.S3LoadTask.TableType.UNIQUE:
        create_table_ddl += f'unique key({task.sort_key})\n'
    else:
        raise Exception(f'Unknown table data model: {task.type!r}')

    if not task.bucket_key:
        raise Exception(f'Unknown table bucket key: {task.bucket_key!r}')

    create_table_ddl += f'distributed by hash({task.bucket_key}) buckets 3\n'
    create_table_ddl += f'properties\n(\n'
    create_table_ddl += f'    "replication_allocation" = "tag.location.group_stream:3"\n'
    create_table_ddl += f')'

    execute_sql(drop_table_ddl, TargetDatabase.DORIS)
    execute_sql(create_table_ddl, TargetDatabase.DORIS)

    sql = textwrap.dedent(f"""
        unload (
            'select * from temp.{task.table.name}'
        )
        to 's3://bi-data-lake/doris/from_redshift/rs_temp/'
        iam_role '{os.getenv('iam_role')}'
        format as parquet
        parallel off
        cleanpath
        maxfilesize as 6GB
    """)
    execute_sql(sql)

    task.attempts += 1
    load_label = f'test__{task}__{task.attempts}'
    load_sql = textwrap.dedent(f'''
        LOAD LABEL {load_label}
        (
            DATA INFILE("s3://bi-data-lake/doris/from_redshift/rs_temp/000.parquet")
            INTO TABLE {task}
            FORMAT AS parquet
            (
                {", ".join(row[0] for row in columns)}
            )
        )
        WITH S3
        (
            "AWS_ENDPOINT"   = "http://s3.cn-northwest-1.amazonaws.com.cn",
            "AWS_ACCESS_KEY" = "{os.getenv("AWS_ACCESS_KEY")}",
            "AWS_SECRET_KEY" = "{os.getenv("AWS_SECRET_KEY")}",
            "AWS_REGION"     = "cn-northwest-1"
        )
    ''')
    execute_sql(load_sql, TargetDatabase.DORIS)

    task.load_label = load_label
    task.save()

    return redirect(reverse('admin:doris_s3loadtask_change', args=(task_id,)))


def query_progress_s3_load_task(request, task_id):
    task: models.S3LoadTask = models.S3LoadTask.objects.select_related('table').get(id=task_id)

    query_load_progress_sql = f'SHOW LOAD WHERE LABEL = "{task.load_label}" order by CreateTime desc limit 1\n'
    rows = execute_sql(query_load_progress_sql, TargetDatabase.DORIS, ret_val=True)
    messages.info(request, mark_safe(f'<pre>{json.dumps(rows, indent=4, ensure_ascii=False)}</pre>'))

    return redirect(reverse('admin:doris_s3loadtask_change', args=(task_id,)))


def refresh_table_list(request):
    dns = os.getenv('dns')

    with psycopg2.connect(dns) as conn:
        with conn.cursor() as cursor:
            sql = textwrap.dedent(f"""
                select table_name from svv_all_tables where schema_name = 'temp'
            """)
            print(sql)
            cursor.execute(sql)
            tables = [
                models.Table(name=row[0]) for row in cursor.fetchall()
            ]
            models.Table.objects.all().delete()
            models.Table.objects.bulk_create(tables)

    return redirect(reverse('admin:doris_table_changelist'))


def create_table(request, table_id):
    table = models.Table.objects.get(id=table_id)

    load_task = models.S3LoadTask.objects.create(table=table)

    messages.info(request, f'Created task {load_task!r}')

    return redirect(reverse('admin:doris_s3loadtask_change', args=(load_task.id,)))
