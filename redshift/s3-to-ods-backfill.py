import textwrap

from utils import sql as sqlutil


def main():
    table_names = [
        # 'order_product',
        'orders',
        # 'payment_entrance',
        # 'payment_flow',
        # 'restaurant_order',
        # 'restaurant_payment_record',
        # 'user_order',
        # 'user_transaction',
    ]
    for table_name in table_names:
        s3_sql = textwrap.dedent(f"""
            select column_name from svv_all_columns
            where schema_name = 'emr' and table_name = 'cafeteria_order_system_{table_name}'
        """)
        ods_sql = textwrap.dedent(f"""
            select column_name from svv_all_columns
            where schema_name = 'ods' and table_name = 'cafeteria_order_system_{table_name}'
        """)
        result = sqlutil.execute_sql(s3_sql, sqlutil.TargetDatabase.REDSHIFT, ret_val=True)
        s3_columns = {row[0] for row in result}
        assert s3_columns
        result = sqlutil.execute_sql(ods_sql, sqlutil.TargetDatabase.REDSHIFT, ret_val=True)
        ods_columns = {row[0] for row in result}
        assert ods_columns
        inc_columns = s3_columns.intersection(ods_columns)
        assert inc_columns
        insert_sql = f"insert into ods.cafeteria_order_system_{table_name} ({','.join(inc_columns)}) select {','.join(inc_columns)} from emr.cafeteria_order_system_{table_name} a where len(event_time) >= 13 and event_time between '2025/02/18/02' and '2025/02/18/07' and not exists(select 1 from ods.cafeteria_order_system_{table_name} b where a.id = b.id)"
        sqlutil.execute_sql(insert_sql, sqlutil.TargetDatabase.REDSHIFT)


if __name__ == '__main__':
    main()
