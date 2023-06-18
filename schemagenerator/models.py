from enum import Enum

from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe


class DbConn(models.Model):
    class Meta:
        verbose_name = '数据库连接'
        verbose_name_plural = '数据库连接'
        ordering = ('name', )

    class DbType(models.TextChoices):
        MYSQL = 'mysql', 'MySQL'
        POSTGRESQL = 'postgres', 'PostgreSQL'

    name = models.CharField('数据库', max_length=128, unique=True)  # TODO MySQL从数据库地址截取 pg库必填
    db_type = models.CharField('类型', max_length=16, choices=DbType.choices, default=DbType.POSTGRESQL.value)
    dns = models.CharField('地址', max_length=256)
    port = models.SmallIntegerField('端口号', default=5432)
    user = models.CharField('用户', max_length=256)
    password = models.CharField('密码', max_length=256)
    schema = models.CharField('源表Schema', max_length=128, default='public')

    target_schema = models.CharField('目标表Schema', max_length=128, blank=True, default='temp', help_text='可选参数 默认为：temp')
    target_table_name_prefix = models.CharField('目标表前缀', max_length=128, blank=True, help_text='可选参数 默认为：数据库 + _')
    s3_path = models.CharField('外部表Location', max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/admin/{self._meta.app_label}/{self._meta.model_name}/{self.id}/change/'

    def server_address(self):
        return f'{DbConn.DbType.MYSQL.value if self.db_type == DbConn.DbType.MYSQL.value else DbConn.DbType.POSTGRESQL.value}://' \
               f'{self.user}:{self.password}@{self.dns}:{self.port}/{self.name}'

    @admin.display(description='操作')
    def html_actions(self):
        buttons = []

        url = reverse('schemagenerator:db_tables', args=(self.id, ))
        buttons.append(f'<a href="{url}">表</a>')

        url = reverse('dms:refresh_endpoints')
        buttons.append(f'<a href="{url}?server_name={self.dns}">端点</a>')

        url = reverse(f'admin:{self._meta.app_label}_task_add')
        buttons.append(f'<a href="{url}?conn={self.id}">添加任务</a>')

        return mark_safe(' / '.join(buttons))

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.target_table_name_prefix:
            self.target_table_name_prefix = f'{self.name}_'
        super().save(force_insert, force_update, using, update_fields)


class Table(models.Model):
    class Meta:
        verbose_name = '表'
        verbose_name_plural = '表'
        ordering = ('conn', 'name', )
        unique_together = ('conn', 'name', )

    name = models.CharField('表', max_length=128)
    conn = models.ForeignKey(DbConn, verbose_name='数据库地址', on_delete=models.CASCADE, related_name='db_tables')

    def __str__(self):
        return self.name


class Task(models.Model):
    class Meta:
        verbose_name = '任务'
        verbose_name_plural = '任务'
        ordering = ('name', )

    class StatusEnum(Enum):
        CREATED = '已创建'
        RUNNING = '运行中...'
        COMPLETED = '已完成'

    name = models.CharField('名称', max_length=128)
    conn = models.ForeignKey(DbConn, verbose_name='数据库', on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField('状态', max_length=32, default=StatusEnum.CREATED.name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/{self._meta.app_label}/{self._meta.model_name}/{self.id}/change/'

    @admin.display(description='操作')
    def html_actions(self):
        buttons = []

        url = reverse('dms:refresh_endpoints')
        buttons.append(f'<a href="{url}?server_name={self.conn.dns}">端点</a>')

        return mark_safe(' / '.join(buttons))


class TaskTable(models.Model):
    class Meta:
        verbose_name = '表'
        verbose_name_plural = '表'

    task = models.ForeignKey(Task, verbose_name='任务', on_delete=models.CASCADE, related_name='sync_tables')
    table = models.ForeignKey(Table, verbose_name='表', on_delete=models.CASCADE, related_name='task_tables')

    def __str__(self):
        return self.table.name
