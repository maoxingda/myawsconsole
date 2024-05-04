from django.db import models
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe


class S3LoadTask(models.Model):
    class Meta:
        verbose_name = 'S3 LOAD'
        verbose_name_plural = 'S3 LOAD'

    class TableType(models.TextChoices):
        DETAIL = 'd', '明细模型'
        AGG    = 'a', '聚合模型'
        UNIQUE = 'u', '主键模型'

    table = models.ForeignKey('Table', verbose_name='表', null=True, on_delete=models.SET_NULL)

    type = models.CharField('模型', max_length=1, choices=TableType.choices, default=TableType.DETAIL)
    sort_key = models.CharField('排序键', max_length=256)
    bucket_key = models.CharField('分桶键', max_length=256)

    attempts = models.SmallIntegerField('执行次数', editable=False)
    load_label = models.CharField(editable=False, max_length=128)

    def __str__(self):
        return self.table.name if self.table else str(self.id)

    @admin.display(description='操作')
    def html_actions(self):
        buttons = []

        if self.id:
            url = reverse('doris:start_s3_load_task', args=(self.id,))
            buttons.append(f'<a href="{url}">启动</a>')

            url = reverse('doris:query_progress_s3_load_task', args=(self.id,))
            buttons.append(f'<a href="{url}">查询进度</a>')

        return mark_safe('&emsp;&emsp;'.join(buttons))


class Table(models.Model):
    class Meta:
        verbose_name = '表'
        verbose_name_plural = '表'
        ordering = ('name', )

    name = models.CharField('表', max_length=128)

    def __str__(self):
        return self.name

    @admin.display(description='操作')
    def html_actions(self):
        buttons = []

        if self.id:
            url = reverse('doris:create_table', args=(self.id,))
            buttons.append(f'<a href="{url}">create table</a>')

        return mark_safe('&emsp;&emsp'.join(buttons))
