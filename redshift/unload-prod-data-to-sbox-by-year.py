import concurrent.futures
import hashlib
import os
import textwrap
import threading
import time
from datetime import datetime, timedelta, timezone
from enum import Enum

import boto3
import psycopg2
import pymysql
import typer


class db(Enum):
    DORIS = 0
    REDSHIFT = 1


def execute_sql(
    stmt: str,
    tgt_db: db = db.REDSHIFT,
    ret_val: bool = False,
    doris_db="test",
):
    exec_sql_start = time.time()
    if tgt_db == db.REDSHIFT:
        dns = os.getenv("dns")  # noqa: SIM112
        with psycopg2.connect(dns) as conn:  # noqa: SIM117
            with conn.cursor() as cursor:
                typer.echo(stmt)
                cursor.execute(stmt)
                elapsed = int((time.time() - exec_sql_start) / 60)
                typer.echo(f"elapsed {elapsed} minutes")
                typer.echo("-" * 128)
                if ret_val:
                    return cursor.fetchall()
    elif tgt_db == db.DORIS:
        config = {
            "user": os.getenv("doris_user"),  # noqa: SIM112
            "password": os.getenv("password"),  # noqa: SIM112
            "host": os.getenv("doris_host"),  # noqa: SIM112
            "port": int(os.getenv("doris_port")),  # noqa: SIM112
            "database": doris_db,
            # "cursorclass": pymysql.cursors.DictCursor,
        }
        with pymysql.connect(**config) as conn:  # noqa: SIM117
            with conn.cursor() as cursor:
                with stdout_lock:
                    typer.echo(stmt)

                cursor.execute(stmt)

                rows = cursor.fetchall()

                elapsed = int((time.time() - exec_sql_start) / 60)
                with stdout_lock:
                    typer.echo(f"elapsed {elapsed} minutes")
                    typer.echo("-" * 128)

                if ret_val:
                    return rows
    else:
        raise Exception(f"Unknown database type: {tgt_db!r}")


def get_table_columns(full_table_name):
    schema_name, table_name = full_table_name.split(".")

    columns = execute_sql(
        f"select column_name from information_schema.columns "
        f"where table_schema = '{schema_name}' and table_name = '{table_name}'",
        tgt_db=db.DORIS,
        ret_val=True,
    )

    return ", ".join(col[0] for col in columns)


def get_sql_hash(sql_text):
    return hashlib.md5(sql_text.encode("utf-8")).hexdigest()


def main(
    full_table_name: str = typer.Option(..., "--full-table-name", help="Full name of the table"),
    partition_column: str = typer.Option(None, "--partition-column", help="Partition column name"),
    s3_key_prefix: str = typer.Option(..., "--s3-key-prefix", help="S3 key prefix for unload/load"),
    skip_unload: bool = typer.Option(False, "--skip-unload/--no-skip-unload", help="Skip the unload step"),
    skip_load: bool = typer.Option(False, "--skip-load/--no-skip-load", help="Skip the load step"),
    unload_parallelism: int = typer.Option(1, "--unload-parallelism", help="Parallelism for unload operation"),
    load_parallelism: int = typer.Option(16, "--load-parallelism", help="Parallelism for load operation"),
    try_unload: bool = typer.Option(False, "--try-unload/--no-try-unload", help="Attempt unload operation"),
    try_load: bool = typer.Option(False, "--try-load/--no-try-load", help="Attempt load operation"),
):
    schema_name, table_name = full_table_name.split(".")
    if s3_key_prefix.endswith("/"):
        s3_key_prefix = s3_key_prefix[:-1]

    if not os.path.exists(f"{full_table_name}.unload.ck"):
        with open(f"{full_table_name}.unload.ck", "w") as f:
            f.write("")

    if not os.path.exists(f"{full_table_name}.load.ck"):
        with open(f"{full_table_name}.load.ck", "w") as f:
            f.write("")

    with open(f"{full_table_name}.unload.ck") as f:
        unload_ck = f.read().split("\n")

    with open(f"{full_table_name}.load.ck") as f:
        load_ck = f.read().split("\n")

    # 按年分区卸载数据，能够保证32个并行度写的文件大小比较合适
    if not skip_unload:
        if partition_column:
            unload_sqls = get_partition_unload_sqls(full_table_name, partition_column, s3_key_prefix)
        else:
            unload_sqls = get_unload_sqls(full_table_name, s3_key_prefix)

        if try_unload:
            unload_sqls = unload_sqls[:1]

        with concurrent.futures.ThreadPoolExecutor(max_workers=unload_parallelism) as executor:
            start = time.time()
            future_to_sql = {
                executor.submit(execute_sql, sql, db.REDSHIFT, False, "ignore-db"): sql
                for sql in unload_sqls
                if get_sql_hash(sql) not in unload_ck
            }
            for future in concurrent.futures.as_completed(future_to_sql):
                sql = future_to_sql[future]
                try:
                    future.result()
                    with open(f"{full_table_name}.unload.ck", "a") as f:
                        f.write(get_sql_hash(sql) + "\n")
                except Exception as exc:
                    typer.echo(f"{sql}\ngenerated an exception: {exc}", err=True)

            elapsed = int((time.time() - start) / 60)
            typer.echo(f"{full_table_name} unload done, elapsed {elapsed} minutes.")
    else:
        typer.echo("skip unload", err=True)

    # 加载数据
    if not skip_load:
        table_columns = get_table_columns(full_table_name)
        s3 = boto3.client("s3", region_name="cn-northwest-1")
        paginator = s3.get_paginator("list_objects_v2")
        with concurrent.futures.ThreadPoolExecutor(max_workers=load_parallelism) as executor:
            load_sqls = []
            for page in paginator.paginate(
                Bucket=f"{os.environ['S3_BUCKET_NAME']}", Prefix=f"{s3_key_prefix}/{schema_name}/{table_name}/"
            ):
                if "Contents" not in page:
                    continue

                for obj in page["Contents"]:
                    if not obj["Size"] > 0:
                        continue

                    sql = textwrap.dedent(f"""
                        insert into {full_table_name} ({table_columns}) select {table_columns}
                        from s3(
                            "URI"            = "s3://{os.environ["S3_BUCKET_NAME"]}/{obj["Key"]}",
                            "s3.access_key"  = "{os.environ["AWS_ACCESS_KEY"]}",
                            "s3.secret_key"  = "{os.environ["AWS_SECRET_KEY"]}",
                            "format"         = "parquet",
                            "use_path_style" = "true",
                            "s3.endpoint"    = "{os.environ["S3_ENDPOINT"]}",
                            "s3.region"      = "{os.environ["S3_REGION"]}"
                        )
                    """)
                    # typer.echo(sql)
                    # typer.echo("-" * 128)
                    load_sqls.append(sql)

            if try_load:
                load_sqls = load_sqls[:1]

            start = time.time()
            future_to_sql = {
                executor.submit(execute_sql, sql, db.DORIS, False, doris_db=schema_name): sql
                for sql in load_sqls
                if get_sql_hash(sql) not in load_ck
            }
            for future in concurrent.futures.as_completed(future_to_sql):
                sql = future_to_sql[future]
                try:
                    future.result()

                    with open(f"{full_table_name}.load.ck", "a") as f:
                        f.write(f"{get_sql_hash(sql)}\n")
                except Exception as exc:
                    typer.echo(f"{sql}\ngenerated an exception: {exc}", err=True)

            elapsed = int((time.time() - start) / 60)
            typer.echo(f"{full_table_name} load done, elapsed {elapsed} minutes.", err=True)
    else:
        typer.echo("skip load", err=True)


def get_unload_sqls(full_table_name, s3_key_prefix):
    sql = textwrap.dedent(f"""
        unload (
            'select * from {full_table_name}'
        )
        to 's3://{os.environ["S3_BUCKET_NAME"]}/{s3_key_prefix}/{full_table_name.split(".")[0]}/{full_table_name.split(".")[1]}/'
        iam_role '{os.getenv("iam_role")}'
        format as parquet
        parallel off
        MAXFILESIZE 512MB
        cleanpath
    """)  # noqa: SIM112, E501

    return [sql]


def get_partition_unload_sqls(full_table_name, partition_column, s3_key_prefix):
    min_partition_val = execute_sql(
        f"select min({partition_column}) from {full_table_name}", tgt_db=db.REDSHIFT, ret_val=True
    )[0][0]
    min_partition_val = f"{min_partition_val.year}-01-01"
    min_partition_val = datetime.strptime(min_partition_val, "%Y-%m-%d")
    today = datetime.now(timezone.utc) + timedelta(hours=8)
    unload_sqls = []
    cur_partition_val = min_partition_val
    while cur_partition_val.year <= today.year:
        upper_bound = cur_partition_val.replace(year=cur_partition_val.year + 1)
        sql = textwrap.dedent(f"""
                unload (
                    'select *, {cur_partition_val.year} as year from {full_table_name} where {partition_column} >= ''{cur_partition_val}'' and {partition_column} < ''{upper_bound}'''
                )
                to 's3://{os.environ["S3_BUCKET_NAME"]}/{s3_key_prefix}/{full_table_name.split(".")[0]}/{full_table_name.split(".")[1]}/'
                iam_role '{os.getenv("iam_role")}'
                format as parquet
                partition by (year)
                parallel on
                MAXFILESIZE 512MB
                cleanpath
            """)  # noqa: SIM112, E501
        # typer.echo(sql)
        # typer.echo("-" * 128)
        cur_partition_val = upper_bound
        unload_sqls.append(sql)
    return unload_sqls


if __name__ == "__main__":
    stdout_lock = threading.Lock()
    typer.run(main)
