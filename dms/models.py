from django.db import models


class Task(models.Model):
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'

    name = models.CharField('名称', max_length=255, unique=True)
    url = models.URLField(max_length=255)
    table_mappings = models.JSONField('表映射', max_length=32768, default=dict)

    def __str__(self):
        return self.name


class Endpoint(models.Model):
    class Meta:
        verbose_name = '端点'
        verbose_name_plural = '端点'

    identifier = models.CharField('ID', max_length=255, unique=True)
    arn = models.CharField('ARN', max_length=255)
    database = models.CharField('数据库', max_length=32, null=True)
    server_name = models.CharField('数据库地址', max_length=255)
    url = models.URLField(max_length=255)

    def __str__(self):
        return self.identifier
