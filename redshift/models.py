from datetime import datetime, timedelta

from django.db import models
from django_extensions.db.models import TimeStampedModel


class Cluster(models.Model):
    class Meta:
        verbose_name = '集群'
        verbose_name_plural = '集群'

    identifier = models.CharField('集群', max_length=128)

    def __str__(self):
        return self.identifier


class Snapshot(models.Model):
    class Meta:
        verbose_name = '快照'
        verbose_name_plural = '快照'
        ordering = (
            '-create_time',
        )

    cluster = models.CharField('集群', max_length=128)
    identifier = models.CharField('快照', max_length=128)

    create_time = models.DateTimeField('创建时间')
    create_time_str = models.CharField(max_length=32)

    # UI字段
    start_date = models.DateField('开始日期', blank=True, null=True)
    end_date = models.DateField('结束日期', blank=True, null=True)

    def __str__(self):
        suffix = self.identifier[-19:]
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

    name = models.CharField('名称', max_length=128)
    snapshot = models.ForeignKey(Snapshot, verbose_name='快照', null=True, on_delete=models.SET_NULL)
    tables = models.ManyToManyField(Table, verbose_name='表')
    is_nofity = models.BooleanField('是否发送完成通知', default=True)

    def __str__(self):
        return self.name


class RestoreClusterTask(TimeStampedModel):
    class Meta:
        verbose_name = '恢复集群任务'
        verbose_name_plural = '恢复集群任务'

    name = models.CharField('名称', max_length=128)
    snapshot = models.ForeignKey(Snapshot, verbose_name='快照', null=True, on_delete=models.SET_NULL)
    is_nofity = models.BooleanField('是否发送完成通知', default=True)

    def __str__(self):
        return self.name
