from django.conf import settings
from django.db import models


class Task(models.Model):
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ('name', )

    # 数据字段
    name = models.CharField('名称', max_length=255, unique=True)
    arn = models.CharField('arn', max_length=255)
    url = models.URLField(max_length=255)
    table_mappings = models.JSONField('表映射', max_length=32768, default=dict)
    source_endpoint_arn = models.CharField('源端点arn', max_length=255, null=True)

    # UI字段
    table_name = models.CharField('表名称', max_length=255)

    def __str__(self):
        return self.name.replace('-' + settings.REPLICATION_TASK_SUFFIX, '')


class Table(models.Model):
    class Meta:
        verbose_name = '表'
        verbose_name_plural = '表'
        ordering = ('name', )
        unique_together = ('task_name', 'schema', 'name',)

    name = models.CharField('名称', max_length=255)
    schema = models.CharField(max_length=32)
    task_name = models.CharField('任务名称', max_length=255, null=True)
    task = models.ForeignKey(to=Task, on_delete=models.CASCADE, related_name='tables', verbose_name='任务', null=True)

    def __str__(self):
        return self.name


class Endpoint(models.Model):
    class Meta:
        verbose_name = '端点'
        verbose_name_plural = '端点'
        ordering = ('identifier', 'database', )

    # 数据字段
    identifier = models.CharField('ID', max_length=255, unique=True)
    arn = models.CharField('ARN', max_length=255)
    database = models.CharField('数据库', max_length=32, null=True)
    url = models.URLField(max_length=255)

    # UI字段
    server_name = models.CharField('数据库地址', max_length=255)

    def __str__(self):
        return self.identifier.replace('-' + settings.ENDPOINT_SUFFIX, '')
