import json

from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from common.admin import CommonAdmin
from dms.models import Task, Endpoint
from dms.views import refresh_endpoints, refresh_tasks


@admin.register(Task)
class TaskAdmin(CommonAdmin):
    list_display = ('name', 'html_actions', )
    list_display_links = ('name', )
    readonly_fields = ('format_table_mappings', )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_fields(self, request, obj=None):
        fields = []
        if obj:
            fields.append('name')
            fields.append('format_table_mappings')
        else:
            fields.append('table_name')
        return fields

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{obj.url}">AWS控制台</a>',
        ]

        return mark_safe(' / '.join(buttons))

    @admin.display(description='表映射')
    def format_table_mappings(self, obj):
        if obj.id:
            return mark_safe(f'<pre>{json.dumps(json.loads(obj.table_mappings), indent=2)}</pre>')

    def my_handler(self, request):
        return refresh_tasks(request)


@admin.register(Endpoint)
class EndpointAdmin(CommonAdmin):
    list_display = ('identifier', 'database', 'html_actions', )
    fields = ('server_name', )

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{reverse("dms:refresh_tasks")}?endpoint_id={obj.id}">DMS任务</a>',
            f'<a href="{obj.url}">AWS控制台</a>',
        ]

        return mark_safe(' / '.join(buttons))

    def my_handler(self, request):
        return refresh_endpoints(request)
