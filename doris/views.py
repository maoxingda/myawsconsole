import json
import time
import os
import re
import textwrap
from pprint import pprint

import boto3
import mysql.connector
import psycopg2
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe

from doris import models
from redshift.util.corp_wechat import send_message
from utils.sql import execute_sql


def start_s3_load_task(request, task_id):
    task: models.S3LoadTask = models.S3LoadTask.objects.select_related('table').get(id=task_id)
    table = task.table

    if task.is_create_table:
        sql = textwrap.dedent(f"""
                select column_name, data_type, character_maximum_length, numeric_precision, numeric_scale 
                from svv_all_columns where schema_name = 'doris_temp' and table_name = '{table.name}'
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
            elif data_type == 'timestamp with time zone':
                create_table_ddl += f'    {column_name} datetime'
            elif data_type == 'double precision':
                create_table_ddl += f'    {column_name} double'
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
        if os.getenv('env') == 'prod':
            create_table_ddl += f'    "replication_allocation" = "tag.location.group_stream:1"\n'
        else:
            create_table_ddl += f'    "replication_allocation" = "tag.location.default:1"\n'
        create_table_ddl += f')'

        execute_sql(drop_table_ddl, TargetDatabase.DORIS)
        execute_sql(create_table_ddl, TargetDatabase.DORIS)

    bucket_name = 'bi-data-lake' if os.getenv('env') == 'prod' else 'bi-data-store'

    if task.is_unload_data:
        sql = textwrap.dedent(f"""
            unload (
                'select * from doris_temp.{task.table.name}'
            )
            to 's3://{bucket_name}/doris/from_redshift/{task.table.name}/'
            iam_role '{os.getenv('iam_role')}'
            format as parquet
            cleanpath
        """)
        execute_sql(sql)

    if task.is_load_data:
        task.attempts += 1
        s3 = boto3.resource('s3', region_name='cn-northwest-1')
        bucket = s3.Bucket(bucket_name)
        for i, obj in enumerate(bucket.objects.filter(Prefix=f'doris/from_redshift/{task.table.name}'), start=1):
            load_label = f'test__{task}__{task.attempts}__{i}'
            load_sql = textwrap.dedent(f'''
                LOAD LABEL {load_label}
                (
                    DATA INFILE("s3://{bucket_name}/doris/from_redshift/{task.table.name}/{os.path.basename(obj.key)}")
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

        while True:
            query_load_progress_sql = f'SHOW LOAD WHERE LABEL = "{task.load_label}" order by CreateTime desc limit 1\n'
            rows = execute_sql(query_load_progress_sql, TargetDatabase.DORIS, ret_val=True)
            if rows[0].get('State') in ('FINISHED', 'CANCELLED'):
                send_message(f'###### Doris load 任务：<font color="info">test.{task}</font> 完成')
                break
            else:
                time.sleep(5)

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
                select table_name from svv_all_tables where schema_name = 'doris_temp'
            """)
            print(sql)
            cursor.execute(sql)
            tables = [
                models.Table(name=row[0])
                for row in cursor.fetchall()
                if not models.Table.objects.filter(name=row[0]).exists()
            ]
            models.Table.objects.bulk_create(tables)

    return redirect(reverse('admin:doris_table_changelist'))


def create_task(request, table_id):
    table = models.Table.objects.get(id=table_id)

    sql = f"select column_name from svv_redshift_columns where schema_name = 'doris_temp' and table_name = '{table.name}'"
    print(sql)
    rows = execute_sql(sql, TargetDatabase.REDSHIFT, ret_val=True)
    column_name = rows[0][0]

    load_task = models.S3LoadTask.objects.create(table=table, sort_key=column_name, bucket_key=column_name)

    messages.info(request, f'Created task {load_task!r}')

    return redirect(reverse('admin:doris_s3loadtask_change', args=(load_task.id,)))


def query_columns(request, task_id):
    load_task = models.S3LoadTask.objects.get(pk=task_id)

    sql = f"select column_name from svv_redshift_columns where schema_name = 'doris_temp' and table_name = '{load_task.table}'"
    print(sql)
    rows = execute_sql(sql, TargetDatabase.REDSHIFT, ret_val=True)
    for row in rows:
        column_name = row[0]
        messages.info(request, f" {column_name}")

    return redirect(reverse('admin:doris_s3loadtask_change', args=(load_task.id,)))


def refresh_doris_db(request, task_id):
    load_task = models.S3LoadTask.objects.get(pk=task_id)

    sql = f"show databases"
    rows = execute_sql(sql, TargetDatabase.DORIS, ret_val=True)

    models.DorisDb.objects.all().delete()
    models.DorisDb.objects.bulk_create(
        models.DorisDb(name=row['Database']) for row in rows
    )

    messages.success(request, f'刷新数据库成功')

    return redirect(reverse('admin:doris_s3loadtask_change', args=(load_task.id,)))


def routineload_refresh(request):
    rls = []
    dbs = models.DorisDb.objects.all()
    for db in dbs:
        routine_loads = execute_sql(
            f'show all routine load',
            TargetDatabase.DORIS, doris_db=db.name, ret_val=True
        )
        for rl in routine_loads:
            if rl['State'] == 'STOPPED':
                continue
            rls.append(
                models.RoutineLoad(
                    name=rl['Name'],
                    state=rl['State'],
                    db=db,
                )
            )

    models.RoutineLoad.objects.all().delete()
    models.RoutineLoad.objects.bulk_create(rls)

    return redirect(reverse('admin:doris_routineload_changelist'))


def resume_routine_load(routine_load: models.RoutineLoad):
    execute_sql(f'resume routine load for {routine_load.name}', TargetDatabase.DORIS, doris_db=routine_load.db.name)


def recreate_routine_load(routine_load: models.RoutineLoad):
    def get_routine_load_live_state():
        state = execute_sql(
            f'show routine load for {routine_load.name}',
            TargetDatabase.DORIS, doris_db=routine_load.db.name, ret_val=True
        )[0]['State']
        return state

    if get_routine_load_live_state() != 'STOPPED':
        sql = f'stop routine load for {routine_load.name}'
        execute_sql(sql, TargetDatabase.DORIS, doris_db=routine_load.db.name)

    sql = f'show create routine load for {routine_load.name}'
    sql = execute_sql(sql, TargetDatabase.DORIS, doris_db=routine_load.db.name, ret_val=True)[0]['CreateStmt']
    execute_sql(f'stop routine load for {routine_load.name}', TargetDatabase.DORIS, doris_db=routine_load.db.name)
    execute_sql(sql, TargetDatabase.DORIS, doris_db=routine_load.db.name)


def routineload_resume(request, pk):
    routine_load = models.RoutineLoad.objects.get(pk=pk)

    resume_routine_load(routine_load)

    return redirect(reverse('admin:doris_routineload_change', args=(routine_load.id,)))


def routineload_recreate(request, pk):
    routine_load = models.RoutineLoad.objects.get(pk=pk)

    recreate_routine_load(routine_load)

    return redirect(reverse('admin:doris_routineload_change', args=(routine_load.id,)))
