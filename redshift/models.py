from datetime import datetime, timedelta
from enum import Enum

from django.db import models
from django_extensions.db.models import TimeStampedModel


class Cluster(models.Model):
    class Meta:
        verbose_name = '集群'
        verbose_name_plural = '集群'

    identifier = models.CharField('集群', max_length=128, unique=True)

    def __str__(self):
        return self.identifier


class Snapshot(models.Model):
    class Meta:
        verbose_name = '快照'
        verbose_name_plural = '快照'
        ordering = (
            '-create_time',
        )
        unique_together = ('cluster', 'identifier',)

    cluster = models.CharField('集群', max_length=128, editable=False)
    identifier = models.CharField('快照', max_length=128, editable=False)

    create_time = models.DateTimeField('创建时间', editable=False)
    create_time_str = models.CharField(max_length=32, editable=False)

    # UI字段
    start_date = models.DateField('开始日期', blank=True, null=True)
    end_date = models.DateField('结束日期', blank=True, null=True)

    def __str__(self):
        suffix = self.identifier[-23:-4]
        suffix_offset = datetime.strptime(suffix, '%Y-%m-%d-%H-%M-%S') + timedelta(hours=8)
        return self.identifier[:-19] + suffix_offset.strftime('%Y-%m-%d-%H-%M-%S')


class Table(models.Model):
    class Meta:
        verbose_name = '表'
        verbose_name_plural = '表'
        ordering = (
            'name',
        )

    name = models.CharField('名称', max_length=255, unique=True)
    schema = models.CharField(max_length=32)

    def __str__(self):
        return self.name


class RestoreTableTask(TimeStampedModel):
    class Meta:
        verbose_name = '恢复表任务'
        verbose_name_plural = '恢复表任务'

    class StatusEnum(Enum):
        CREATED = '已创建'
        RUNNING = '运行中...'
        COMPLETED = '已完成'

    name = models.CharField('名称', max_length=128)
    snapshot = models.ForeignKey(Snapshot, verbose_name='快照', null=True, on_delete=models.SET_NULL)
    tables = models.ManyToManyField(Table, verbose_name='表')
    is_nofity = models.BooleanField('是否发送完成通知', default=True)
    status = models.CharField('状态', max_length=32, default=StatusEnum.CREATED.name)

    def __str__(self):
        return self.name


class RestoreClusterTask(TimeStampedModel):
    class Meta:
        verbose_name = '恢复集群任务'
        verbose_name_plural = '恢复集群任务'

    class StatusEnum(Enum):
        CREATED = 0
        RUNNING = 1
        COMPELETED = 2

    name = models.CharField('名称', max_length=128)
    snapshot = models.ForeignKey(Snapshot, verbose_name='快照', null=True, on_delete=models.SET_NULL)
    is_nofity = models.BooleanField('是否发送完成通知', default=True)
    status = models.CharField('状态', max_length=32, default=StatusEnum.CREATED.name)

    def __str__(self):
        return self.name


class QueryHistory(TimeStampedModel):
    class Meta:
        verbose_name = '查询历史'
        verbose_name_plural = '查询历史'

    query_id       = models.BigIntegerField('查询ID')
    start_time     = models.DateTimeField('开始时间')
    elapsed        = models.BigIntegerField('耗时', help_text='单位：分钟')
    dashboard_code = models.CharField('报表编码', max_length=16, null=True)
    query_uuid     = models.CharField('查询UUID', max_length=64, null=True)

    def __str__(self):
        return self.query_text
