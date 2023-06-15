from django.db import models


class Task(models.Model):
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'

    # 数据字段
    name = models.CharField('名称', max_length=255, unique=True)
    arn = models.CharField('arn', max_length=255)
    url = models.URLField(max_length=255)
    table_mappings = models.JSONField('表映射', max_length=32768, default=dict)

    # UI字段
    table_name = models.CharField('表名称', max_length=255)

    def __str__(self):
        return self.name


class Table(models.Model):
    class Meta:
        verbose_name = '表'
        verbose_name_plural = '表'
        ordering = ('name', )

    name = models.CharField('名称', max_length=255, unique=True)
    schema = models.CharField(max_length=32)

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
        return self.identifier
