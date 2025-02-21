from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder


class Task(models.Model):
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ('name',)

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
        ordering = ('name',)
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


class ReplicationTask(models.Model):
    class Meta:
        verbose_name = '复制任务'
        verbose_name_plural = '复制任务'

    migration_type                 = models.CharField(max_length=100)
    recovery_checkpoint            = models.CharField(max_length=255)
    replication_instance_arn       = models.CharField(max_length=255)
    replication_task_arn           = models.CharField(max_length=255)
    replication_task_creation_date = models.DateTimeField(default=timezone.now)
    replication_task_identifier    = models.CharField(max_length=255, unique=True)
    replication_task_settings      = models.JSONField()
    replication_task_start_date    = models.DateTimeField(default=timezone.now)
    replication_task_stats         = models.JSONField(encoder=DjangoJSONEncoder)
    source_endpoint                = models.ForeignKey('ReplicationEndpoint', null=True, on_delete=models.SET_NULL, related_name='source_replication_tasks')
    target_endpoint                = models.ForeignKey('ReplicationEndpoint', null=True, on_delete=models.SET_NULL, related_name='target_replication_tasks')
    status                         = models.CharField(max_length=50)
    table_mappings                 = models.JSONField()

    def __str__(self):
        return self.replication_task_identifier


class ReplicationEndpoint(models.Model):
    class Meta:
        verbose_name = '端点v2'
        verbose_name_plural = '端点v2'

    endpoint_arn        = models.CharField(max_length=255, unique=True)
    endpoint_identifier = models.CharField(max_length=255, unique=True)
    endpoint_type       = models.CharField(max_length=50)
    engine_name         = models.CharField(max_length=50)
    engine_display_name = models.CharField(max_length=50)
    status              = models.CharField(max_length=50)
    database_name       = models.CharField(max_length=50)
    server_name         = models.CharField(max_length=50)

    def __str__(self):
        return self.endpoint_identifier
