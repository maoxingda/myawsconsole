import os
from enum import Enum
import mysql.connector
import psycopg2


class TargetDatabase(Enum):
    DORIS = 0
    REDSHIFT = 1


def execute_sql(
        sql: str,
        tgt_db: TargetDatabase = TargetDatabase.REDSHIFT,
        ret_val: bool = False,
        doris_db='test',
        dictionary=True
):
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
            'user': os.getenv('doris_user'),
            'password': os.getenv('password'),
            'host': os.getenv('doris_host'),
            'port': os.getenv('doris_port'),
            'database': doris_db,
        }
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor(dictionary=dictionary)

        print(sql)
        print('-' * 128)
        cursor.execute(sql)

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        if ret_val:
            return rows
    else:
        raise Exception(f'Unknown database type: {tgt_db!r}')
