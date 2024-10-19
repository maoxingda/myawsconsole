import re
import textwrap

from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.utils.safestring import mark_safe
from kafka.admin import KafkaAdminClient
from kafka import KafkaConsumer, TopicPartition
from datetime import datetime
import json

from msk import models
from utils.sql import execute_sql, TargetDatabase


def refresh_topic_list(request):
    admin_client = KafkaAdminClient(
        bootstrap_servers=['b-1.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092',
                           'b-5.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092',
                           'b-9.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092']
    )
    topics = admin_client.list_topics()
    models.Topic.objects.all().delete()
    models.Topic.objects.bulk_create(
        models.Topic(name=topic)
        for topic in topics if not topic.startswith('__') and not topic.startswith('--')
    )

    return redirect(reverse('admin:msk_topic_changelist'))


def topic_message_out_of_order_upbound(request, pk):
    start = datetime.now()
    action = request.GET.get('action')
    topic = models.Topic.objects.get(pk=pk)
    table_name = re.sub(r'\.|-', '_', topic.name)

    if action == 'sync-data':
        consumer = KafkaConsumer(
            bootstrap_servers=['b-1.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092',
                               'b-5.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092',
                               'b-9.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092'],
            enable_auto_commit=False
        )

        partition = 0
        tp = TopicPartition(topic.name, partition)
        execute_sql(f'drop table if exists msk.{table_name}', tgt_db=TargetDatabase.REDSHIFT)
        execute_sql(f'create table msk.{table_name} (id bigint identity(1, 1), key varchar(255), ts bigint)', tgt_db=TargetDatabase.REDSHIFT)

        start_timestamp = int(topic.start_time.timestamp()) * 1000
        end_timestamp = int(topic.end_time.timestamp()) * 1000

        offsets = consumer.offsets_for_times({tp: start_timestamp})

        if offsets[tp]:
            consumer.assign([tp])
            consumer.seek(tp, offsets[tp].offset)
            print(f"Starting consumption from offset: {offsets[tp].offset}")
            topic.start_offset = offsets[tp].offset

            has_data = False
            event_ts = []
            for message in consumer:
                value = json.loads(message.value.decode('utf-8'))
                event_time = value.get(topic.event_time_field_name, value.get('modify_time'))
                event_time = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')
                event_time = int(event_time.timestamp())
                event_ts.append(f"('{value[topic.key]}',{event_time})")
                if len(event_ts) % 1024 == 0:
                    has_data = True
                    execute_sql(f'insert into msk.{table_name} (key, ts) values {",".join(event_ts)}',
                                tgt_db=TargetDatabase.REDSHIFT)
                    event_ts.clear()
                    elapsed = datetime.now() - start
                    elapsed = int(elapsed.total_seconds()) - 28800
                    elapsed = datetime.fromtimestamp(elapsed).strftime("%H:%M:%S")
                    print(f'msg_ts: {datetime.fromtimestamp(message.timestamp / 1000)}, 耗时：{elapsed}')
                if message.timestamp >= end_timestamp:
                    break
            if event_ts:
                has_data = True
                execute_sql(f'insert into msk.{table_name} (key, ts) values {",".join(event_ts)}',
                            tgt_db=TargetDatabase.REDSHIFT)
            if has_data:
                topic.has_data = True
                topic.save()
        else:
            messages.warning(request, "No offset found for the specified timestamp")
    elif action == 'out-of-order-upbound':
        if topic.has_data:
            sql = textwrap.dedent(f"""
                with
                    t1 as (
                        select id, ts, max(ts) over(
                            order by id 
                            rows between unbounded preceding and current row
                        ) as max_ts
                        from msk.{table_name}
                    )
                select max_ts - ts as diff_ts, id
                from t1
                where diff_ts > 0
                -- group by diff_ts
                order by diff_ts desc
                limit {topic.topn}
            """)

        rows = execute_sql(sql, tgt_db=TargetDatabase.REDSHIFT, ret_val=True)

        for row in rows:
            messages.info(request, f'{str(row[0]):<4}{row[1]}')
    elif action == 'key-out-of-order-upbound':
        if topic.has_data:
            sql = textwrap.dedent(f"""
                with
                    t1 as (
                        select ts, max(ts) over(
                            partition by key
                            order by id 
                            rows between unbounded preceding and current row
                        ) as max_ts
                        from msk.{table_name}
                    )
                select max_ts - ts as diff_ts
                from t1
                where diff_ts > 0
                order by diff_ts desc
                limit {topic.topn}
            """)

            rows = execute_sql(sql, tgt_db=TargetDatabase.REDSHIFT, ret_val=True)

            for row in rows:
                messages.info(request, f'{row[0]}{row[1]}')

            if len(rows) == 0:
                messages.info(request, f'键粒度没有消息乱序')

    elapsed = datetime.now() - start
    elapsed = int(elapsed.total_seconds()) - 28800
    elapsed = datetime.fromtimestamp(elapsed).strftime("%H:%M:%S")

    messages.info(request, f'耗时: {elapsed}')

    return redirect(reverse('admin:msk_topic_change', args=(pk,)))


def topic_message_count(request, pk):
    topic = models.Topic.objects.get(pk=pk)
    table_name = re.sub(r'\.|-', '_', topic.name)

    rows = execute_sql(f'select count(1) from msk.{table_name}', tgt_db=TargetDatabase.REDSHIFT, ret_val=True)

    messages.info(request, f'{rows[0][0]}')

    return redirect(reverse('admin:msk_topic_change', args=(pk,)))


def topic_last_message(request, pk):
    topic = models.Topic.objects.get(pk=pk)
    # 创建 KafkaConsumer 实例
    consumer = KafkaConsumer(
        bootstrap_servers=['b-1.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092',
                           'b-5.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092',
                           'b-9.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092'],
        enable_auto_commit=False
    )

    # 定义主题和分区
    partition = 0

    # 创建 TopicPartition 对象
    tp = TopicPartition(topic.name, partition)

    # 获取最新的偏移量
    consumer.assign([tp])
    end_offset = consumer.end_offsets([tp])[tp]

    # 消费最新的消息（从 end_offset - 1 开始）
    if end_offset > 0:
        consumer.seek(tp, end_offset - 1)  # 移动到最后一条消息
        for message in consumer:
            print(f"Partition: {message.partition}, Offset: {message.offset}, Value: {message.value.decode('utf-8')}")
            value = json.loads(message.value.decode('utf-8'))
            value = json.dumps(value, indent=True, ensure_ascii=False)
            messages.info(request, mark_safe(f'<pre>{value}</pre>'))
            break  # 只消费最后一条消息
    else:
        messages.info(request, f'No messages in this partition.')

    return redirect(reverse('admin:msk_topic_change', args=(pk,)))


def check_message_order(request, pk):
    topic = models.Topic.objects.get(pk=pk)
    table_name = re.sub(r'\.|-', '_', topic.name)
    # 创建 KafkaConsumer 实例
    consumer = KafkaConsumer(
        bootstrap_servers=['b-1.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092',
                           'b-5.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092',
                           'b-9.bi-rdw-kafka.6pqqfj.c3.kafka.cn-northwest-1.amazonaws.com.cn:9092'],
        enable_auto_commit=False
    )

    # 定义主题和分区
    partition = 0

    # 创建 TopicPartition 对象
    tp = TopicPartition(topic.name, partition)

    # 获取最新的偏移量
    consumer.assign([tp])
    consumer.seek(tp, topic.start_offset)

    sql = textwrap.dedent(f"""
        select key from msk.{table_name} order by id
    """)

    rows = execute_sql(sql, tgt_db=TargetDatabase.REDSHIFT, ret_val=True)

    for i, message in enumerate(consumer):
        value = json.loads(message.value.decode('utf-8'))
        if str(value[topic.key]) != rows[i][0]:
            messages.error(request, f'{value[topic.key]} != {rows[i][0]}')
            break
        if i + 1 == len(rows):
            break

    return redirect(reverse('admin:msk_topic_change', args=(pk,)))
