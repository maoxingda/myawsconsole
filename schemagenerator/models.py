import json
from enum import Enum

from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe


class TaskTypeEnum(models.TextChoices):
    DATA = 'data', '表数据'
    SCHEMA = 'schema', '表结构'


class DbConn(models.Model):
    class Meta:
        verbose_name = '数据库连接'
        verbose_name_plural = '数据库连接'
        ordering = ('name', )

    class DbType(models.TextChoices):
        MYSQL = 'mysql', 'MySQL'
        POSTGRESQL = 'postgres', 'PostgreSQL'

    user = models.CharField('用户', max_length=256)
    password = models.CharField('密码', max_length=256)
    dns = models.CharField('地址', max_length=256)
    port = models.SmallIntegerField('端口号', default=5432)
    name = models.CharField('数据库', max_length=128, unique=True)  # TODO MySQL从数据库地址截取 pg库必填
    db_type = models.CharField('类型', max_length=16, choices=DbType.choices, default=DbType.POSTGRESQL.value)
    schema = models.CharField('源表Schema', max_length=128, default='public')

    target_schema = models.CharField('目标表Schema', max_length=128, blank=True, default='temp')
    target_table_name_prefix = models.CharField('目标表前缀', max_length=128, blank=True)
    s3_path = models.CharField('外部表Location', max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/admin/{self._meta.app_label}/{self._meta.model_name}/{self.id}/change/'

    def server_address(self):
        protocol = (
            DbConn.DbType.MYSQL.value
            if self.db_type == DbConn.DbType.MYSQL.value
            else DbConn.DbType.POSTGRESQL.value
        )
        return f'{protocol}://{self.user}:{self.password}@{self.dns}:{self.port}/{self.name}'

    @admin.display(description='操作')
    def html_actions(self):
        buttons = []

        url = reverse('schemagenerator:db_tables', args=(self.id, ))
        buttons.append(f'<a href="{url}">表</a>')

        url = reverse('admin:dms_replicationendpoint_changelist')
        buttons.append(f'<a href="{url}?server_name={self.dns}">端点</a>')

        url = reverse(f'admin:{self._meta.app_label}_task_add')
        buttons.append(f'<a href="{url}?conn={self.id}&task_type={TaskTypeEnum.SCHEMA.value}">同步表结构</a>')

        url = reverse(f'admin:{self._meta.app_label}_task_add')
        buttons.append(f'<a href="{url}?conn={self.id}&task_type={TaskTypeEnum.DATA.value}">同步表数据</a>')

        return mark_safe(' / '.join(buttons))


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
        verbose_name        = '任务'
        verbose_name_plural = '任务'
        ordering            = ('-id', )

    class StatusEnum(models.TextChoices):
        CREATED   = 'created'  , '已创建'
        RUNNING   = 'running'  , '运行中...'
        COMPLETED = 'completed', '已完成'

    name = models.CharField('名称', max_length=128)
    conn = models.ForeignKey(DbConn, verbose_name='数据库', on_delete=models.CASCADE, related_name='tasks')
    status = models.CharField('状态', max_length=32, choices=StatusEnum.choices, default=StatusEnum.CREATED.value)
    task_type = models.CharField('任务类型', max_length=32, choices=TaskTypeEnum.choices, default=TaskTypeEnum.SCHEMA.value)

    dms_task_id = models.CharField(max_length=255, null=True, editable=False)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f'/{self._meta.app_label}/{self._meta.model_name}/{self.id}/change/'

    def table_mappins(self):
        table_mappings = {
            'rules': [
                {
                    'rule-type': 'transformation',
                    'rule-id': 1,
                    'rule-name': 1,
                    'rule-target': 'table',
                    'object-locator': {
                        'schema-name': '%',
                        'table-name': '%'
                    },
                    'rule-action': 'add-prefix',
                    'value': self.conn.target_table_name_prefix,
                    'old-value': None
                },
                {
                    'rule-type': 'transformation',
                    'rule-id': 2,
                    'rule-name': 2,
                    'rule-target': 'schema',
                    'object-locator': {
                        'schema-name': '%'
                    },
                    'rule-action': 'rename',
                    'value': self.conn.target_schema,
                    'old-value': None
                }
            ]
        }
        schema_name = self.conn.name if self.conn.db_type == DbConn.DbType.MYSQL.value else self.conn.schema
        for i, task_table in enumerate(self.sync_tables.all()):
            table_mappings['rules'].append({
                'rule-id': 10001 + i,
                'rule-name': 10001 + i,
                'rule-type': 'selection',
                'object-locator': {
                    'schema-name': schema_name,
                    'table-name': task_table.table.name
                },
                'rule-action': 'include'
            })
            if self.task_type == TaskTypeEnum.SCHEMA.value:
                table_mappings['rules'][-1]['filters'] = [
                    {
                        'filter-type': 'source',
                        'column-name': 'id',
                        'filter-conditions': [
                            {
                                'filter-operator': 'null'
                            }
                        ]
                    }
                ]
        return table_mappings

    @admin.display(description='操作')
    def html_actions(self):
        buttons = []

        if self.id and self.status != Task.StatusEnum.RUNNING.value:
            url = reverse('schemagenerator:launch_task', args=(self.id, ))
            text = (
                '启动'
                if self.status == Task.StatusEnum.CREATED.value
                else '重启'
            )
            buttons.append(f'<a href="{url}">{text}</a>')

        if self.status == Task.StatusEnum.COMPLETED.value:
            url = reverse('schemagenerator:download_sql', args=(self.id, ))
            buttons.append(f'<a id="id_download_sql" href="{url}">下载SQL</a>')

            url = reverse('schemagenerator:create_ddl_sql', args=(self.id, ))
            buttons.append(f'<a id="id_download_emr_ddl_sql" href="{url}">下载DDL</a>')

            url = reverse('schemagenerator:update_table_mappings', args=(self.id, ))
            buttons.append(f'<a href="{url}">更新表映射</a>')

        if self.status == Task.StatusEnum.RUNNING.value:
            url = reverse('schemagenerator:update_status', args=(self.id, ))
            buttons.append(f'<a href="{url}">更新状态</a>')

        if self.id:
            url = reverse('schemagenerator:get_table_mappings', args=(self.id, ))
            buttons.append(f'<a href="{url}">获取表映射</a>')

        return mark_safe('&emsp;'.join(buttons))

    @admin.display(description='表映射')
    def fomart_table_mappings(self):
        return mark_safe(f'<pre>{json.dumps(self.table_mappins(), indent=4)}</pre>')


class TaskTable(models.Model):
    class Meta:
        verbose_name = '表'
        verbose_name_plural = '表'

    task = models.ForeignKey(Task, verbose_name='任务', on_delete=models.CASCADE, related_name='sync_tables')
    table = models.ForeignKey(Table, verbose_name='表', on_delete=models.CASCADE, related_name='task_tables')

    def __str__(self):
        return self.table.name
