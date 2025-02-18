import json
import re

import boto3
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from common.admin import CommonAdmin
from dms.models import Task, Endpoint, Table
from dms.views import refresh_endpoints, refresh_tasks, stop_then_resume_task


@admin.register(Task)
class TaskAdmin(CommonAdmin):
    actions = ()
    search_fields = ('name', 'table_name', 'source_endpoint_arn',)
    list_display = ('__str__', 'html_actions',)
    list_display_links = ('__str__',)
    readonly_fields = ('format_table_mappings',)
    list_filter = ('table_name',)

    sync_schema_task_pattern = re.compile(rf'-{settings.REPLICATION_TASK_SUFFIX}$')

    def has_change_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        fields = []
        if obj:
            fields.extend(['name', 'format_table_mappings'])
        else:
            fields.append('table_name')
        return fields

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{reverse("dms:refresh_tables", args=(obj.id,))}">同步的表</a>',
            f'<a href="{obj.url}">AWS控制台</a>',
        ]

        if self.sync_schema_task_pattern.search(obj.name):
            url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete', args=(obj.id,))
            buttons.append(f'<a href="{url}">删除</a>')
            buttons.append(f'🚒')

        return mark_safe(' / '.join(buttons))

    @admin.display(description='表映射')
    def format_table_mappings(self, obj):
        if obj.id:
            return mark_safe(f'<pre>{json.dumps(json.loads(obj.table_mappings), indent=2)}</pre>')

    def my_handler(self, request):
        return refresh_tasks(request)

    def delete_view(self, request, object_id, extra_context=None):
        if request.method == 'POST':
            task = Task.objects.get(id=object_id)
            if self.sync_schema_task_pattern.search(task.name):
                client = boto3.client('dms')
                client.delete_replication_task(ReplicationTaskArn=task.arn)
                waiter = client.get_waiter('replication_task_deleted')
                waiter.wait(Filters=[{'Name': 'replication-task-id', 'Values': [task.name]}])

                client.delete_endpoint(EndpointArn=task.source_endpoint_arn)
        return super().delete_view(request, object_id, extra_context)


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    search_fields = ('name', 'task_name',)
    list_display = ('name', 'schema', 'task_name',)
    list_filter = ('task_name', 'schema',)
    exclude = ('task',)

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


@admin.register(Endpoint)
class EndpointAdmin(CommonAdmin):
    search_fields = ('server_name',)
    list_display = ('__str__', 'database', 'html_actions',)
    fields = ('server_name',)
    actions = ()

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{reverse("dms:refresh_tasks")}?endpoint_id={obj.id}">DMS任务</a>',
            f'<a href="{obj.url}">AWS控制台</a>',
        ]
        sync_schema_source_pattern = re.compile(rf'-{settings.ENDPOINT_SUFFIX}$')
        if sync_schema_source_pattern.search(obj.identifier):
            buttons.append(f'🚒')

        return mark_safe(' / '.join(buttons))

    def my_handler(self, request):
        return refresh_endpoints(request)
