import os
from enum import Enum

import psycopg2

# import mysql.connector
import pymysql


class TargetDatabase(Enum):
    DORIS = 0
    REDSHIFT = 1


def execute_sql(
    sql: str,
    tgt_db: TargetDatabase = TargetDatabase.REDSHIFT,
    ret_val: bool = False,
    doris_db="test",
    dictionary=True,
):
    if tgt_db == TargetDatabase.REDSHIFT:
        dns = os.getenv("dns")  # noqa: SIM112
        with psycopg2.connect(dns) as conn:  # noqa: SIM117
            with conn.cursor() as cursor:
                print(sql)
                print("-" * 128)
                cursor.execute(sql)
                if ret_val:
                    return cursor.fetchall()
    elif tgt_db == TargetDatabase.DORIS:
        config = {
            "user": os.getenv("doris_user"),  # noqa: SIM112
            "password": os.getenv("password"),  # noqa: SIM112
            "host": os.getenv("doris_host"),  # noqa: SIM112
            "port": int(os.getenv("doris_port")),  # noqa: SIM112
            "database": doris_db,
            "cursorclass": pymysql.cursors.DictCursor,
        }
        conn = pymysql.connect(**config)
        cursor = conn.cursor()

        print(sql)
        print("-" * 128)
        cursor.execute(sql)

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        if ret_val:
            return rows
    else:
        raise Exception(f"Unknown database type: {tgt_db!r}")
