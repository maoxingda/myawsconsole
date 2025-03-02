from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe


class DorisDb(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "Doris数据库"

    name = models.CharField(max_length=32, verbose_name="数据库")

    def __str__(self):
        return self.name


class S3LoadTask(models.Model):
    class Meta:
        verbose_name = "S3 LOAD"
        verbose_name_plural = "S3 LOAD"

    class TableType(models.TextChoices):
        DETAIL = "d", "明细模型"
        AGG = "a", "聚合模型"
        UNIQUE = "u", "主键模型"

    table = models.ForeignKey("Table", verbose_name="表", null=True, on_delete=models.SET_NULL)
    doris_db = models.ForeignKey(DorisDb, verbose_name="数据库", null=True, on_delete=models.SET_NULL)

    type = models.CharField("模型", max_length=1, choices=TableType.choices, default=TableType.DETAIL)
    is_create_table = models.BooleanField("建表", default=False)
    is_unload_data = models.BooleanField("卸载数据", default=False)
    is_load_data = models.BooleanField("加载数据", default=False)
    sort_key = models.CharField("排序键", max_length=256, null=True)
    bucket_key = models.CharField("分桶键", max_length=256, null=True)

    attempts = models.SmallIntegerField("执行次数", editable=False, default=0)
    load_label = models.CharField(editable=False, max_length=128, default="")

    def __str__(self):
        return self.table.name if self.table else str(self.id)

    @admin.display(description="操作")
    def html_actions(self):
        buttons = []

        if self.id:
            url = reverse("doris:start_s3_load_task", args=(self.id,))
            buttons.append(f'<a href="{url}">启动</a>')

            url = reverse("doris:query_progress_s3_load_task", args=(self.id,))
            buttons.append(f'<a href="{url}">查询进度</a>')

            url = reverse("doris:query_columns", args=(self.id,))
            buttons.append(f'<a href="{url}">查询列</a>')

            url = reverse("doris:refresh_doris_db", args=(self.id,))
            buttons.append(f'<a href="{url}">刷新数据库</a>')

        return mark_safe("&emsp;&emsp;".join(buttons))


class Table(models.Model):
    class Meta:
        verbose_name = "表"
        verbose_name_plural = "表"
        ordering = ("name",)

    name = models.CharField("表", max_length=128, unique=True)

    def __str__(self):
        return self.name

    @admin.display(description="操作")
    def html_actions(self):
        buttons = []

        if self.id:
            url = reverse("doris:create_task", args=(self.id,))
            buttons.append(f'<a href="{url}">create task</a>')

        return mark_safe("&emsp;&emsp".join(buttons))


class RoutineLoad(models.Model):
    class Meta:
        verbose_name = verbose_name_plural = "例行加载任务"
        unique_together = ("db", "name")
        ordering = ("db", "name")

    name = models.CharField(max_length=32, verbose_name="名称")
    state = models.CharField(max_length=32, verbose_name="状态")
    lag = models.BigIntegerField(verbose_name="延迟", default=0)

    db = models.ForeignKey(DorisDb, verbose_name="数据库", null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.db}.{self.name}"

    @admin.display(description="操作")
    def html_actions(self):
        buttons = []

        if self.id:
            if self.state == "PAUSED":
                url = reverse("doris:routineload_resume", args=(self.id,))
                buttons.append(f'<a href="{url}">恢复</a>')

            url = reverse("doris:routineload_recreate", args=(self.id,))
            buttons.append(f'<a href="{url}">重建</a>')

        return mark_safe("&emsp;&emsp;".join(buttons))
