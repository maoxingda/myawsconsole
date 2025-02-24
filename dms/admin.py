import json
import re

import boto3
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Q

from common.admin import CommonAdmin
from dms.models import Task, Endpoint, Table, ReplicationTask, ReplicationEndpoint
from dms.views import refresh_endpoints, refresh_tasks, stop_then_resume_task


# @admin.register(Task)
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
    exclude = ('task_name',)

    def get_search_results(self, request, queryset, search_term):
        """
        搜索时，排除以“-”开头的搜索词，可以封装为 admin 通用代码
        """
        from django.utils.text import smart_split

        normal_terms = []
        startswith_hyphen_terms = []

        for term in smart_split(search_term):
            if term.startswith('-'):
                startswith_hyphen_terms.append(term[1:])
            else:
                normal_terms.append(term)

        queryset, _ = super().get_search_results(request, queryset, ' '.join(normal_terms))

        for term in startswith_hyphen_terms:
            for search_field in self.get_search_fields(request):
                queryset = queryset.exclude(**{f'{search_field}__iregex': term})

        exclude_condition = Q()

        for term in startswith_hyphen_terms:
            for search_field in self.get_search_fields(request):
                exclude_condition &= Q(**{f'{search_field}__iregex': term})

        queryset = queryset.exclude(exclude_condition)

        return queryset, _

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


# @admin.register(Endpoint)
class EndpointAdmin(CommonAdmin):
    search_fields = ('server_name', 'identifier')
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


@admin.register(ReplicationTask)
class ReplicationTaskAdmin(admin.ModelAdmin):
    sync_schema_task_pattern = re.compile(rf'-{settings.REPLICATION_TASK_SUFFIX}$')

    search_fields = (
        'replication_task_identifier',
    )
    date_hierarchy = 'replication_task_creation_date'
    ordering = (
        'replication_task_identifier',
    )
    list_display = (
        'replication_task_identifier',
        'html_actions',
        # 'migration_type',
        # 'status',
        # 'source_endpoint',
        # 'target_endpoint',
    )
    list_filter = (
        'status',
        'migration_type',
        'replication_instance_arn',
    )
    readonly_fields = (
        'source_endpoint',
        'target_endpoint',
    )

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{reverse("dms:task_tables", args=(obj.id,))}">同步的表</a>',
            f'<a href="{obj.aws_console_url}">AWS控制台</a>',
        ]

        if self.sync_schema_task_pattern.search(obj.replication_task_identifier):
            url = reverse(f'admin:{obj._meta.app_label}_{obj._meta.model_name}_delete', args=(obj.id,))
            buttons.append(f'<a href="{url}">删除</a>')
            buttons.append(f'🚒')

        return mark_safe(' / '.join(buttons))


@admin.register(ReplicationEndpoint)
class ReplicationEndpointAdmin(admin.ModelAdmin):
    search_fields = (
        'endpoint_identifier',
        'database_name',
        'server_name',
    )
    ordering = (
        'endpoint_identifier',
    )
    list_display = (
        'endpoint_identifier',
        'html_actions',
        'endpoint_type',
        'database_name',
        'engine_display_name',
    )
    list_filter = (
        'endpoint_type',
        'engine_name',
    )

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{settings.AWS_DMS_URL}#endpointDetails/{obj.endpoint_identifier}">AWS控制台</a>',
        ]

        if obj.endpoint_type == 'SOURCE':
            url = reverse(f'admin:dms_replicationtask_changelist') + f'?source_endpoint_id={obj.id}'
        else:
            url = reverse(f'admin:dms_replicationtask_changelist') + f'?target_endpoint_id={obj.id}'
        buttons.append(f'<a href="{url}">DMS任务</a>')

        sync_schema_source_pattern = re.compile(rf'-{settings.ENDPOINT_SUFFIX}$')
        if sync_schema_source_pattern.search(obj.endpoint_identifier):
            buttons.append(f'🚒')

        return mark_safe(' / '.join(buttons))
