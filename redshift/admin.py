from django.contrib import admin

from redshift.models import Snapshot, Table, RestoreTableTask


class PermissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Snapshot)
class SnapshotAdmin(PermissionAdmin):
    date_hierarchy = 'create_time'
    search_fields = (
        'create_time_str',
    )
    exclude = (
        'create_time_str',
    )

    def changelist_view(self, request, extra_context=None):
        start_date = request.session.get('start_date')
        end_date = request.session.get('end_date')
        if not extra_context:
            extra_context = {}
        if start_date:
            extra_context['start_date'] = start_date
        if end_date:
            extra_context['end_date'] = end_date
        return super().changelist_view(request, extra_context)


@admin.register(Table)
class TableAdmin(PermissionAdmin):
    search_fields = (
        'name',
    )
    list_filter = (
        'schema',
    )


@admin.register(RestoreTableTask)
class RestorTableTaskAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        'snapshot',
    )
    list_display = (
        'name',
        'snapshot',
    )
    filter_horizontal = (
        'tables',
    )
    # readonly_fields = (
    #     'html_actions',
    # )
    #
    # @admin.display(description='操作')
    # def html_actions(self, obj):
    #     buttons = [
    #         f'<a href="/redshift/api/restore_table_task/{obj.id}/launch/">启动</a>',
    #     ]
    #     return mark_safe('&emsp;'.join(buttons))
