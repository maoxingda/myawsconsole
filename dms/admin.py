import json

from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from dms.models import Task, Endpoint


class PermissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Task)
class TaskAdmin(PermissionAdmin):
    list_display = (
        'name',
        'html_actions',
    )
    fields = (
        'name',
        'format_table_mappings',
    )

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{obj.url}">AWS控制台</a>',
        ]

        return mark_safe(' / '.join(buttons))

    @admin.display(description='表映射')
    def format_table_mappings(self, obj):
        return mark_safe(f'<pre>{json.dumps(json.loads(obj.table_mappings), indent=2)}</pre>')

    def changelist_view(self, request, extra_context=None):
        search_table = request.session.get('search_table')
        if not extra_context:
            extra_context = {}
        if search_table:
            extra_context['search_table'] = search_table
        return super().changelist_view(request, extra_context)


@admin.register(Endpoint)
class EndpointAdmin(PermissionAdmin):
    list_display = (
        'identifier',
        'database',
        'html_actions',
    )

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = [
            f'<a href="{reverse("dms:refresh_tasks")}?endpoint_id={obj.id}">DMS任务</a>',
            f'<a href="{obj.url}">AWS控制台</a>',
        ]

        return mark_safe(' / '.join(buttons))

    def changelist_view(self, request, extra_context=None):
        server_name = request.session.get('server_name')
        if not extra_context:
            extra_context = {}
        if server_name:
            extra_context['server_name'] = server_name
        return super().changelist_view(request, extra_context)
