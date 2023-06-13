import boto3
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from redshift.models import Snapshot, Table, RestoreTableTask, RestoreClusterTask, Cluster


admin.site.site_title = '我的AWS控制台'
admin.site.site_header = '我的AWS控制台'


class PermissionAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Cluster)
class ClusterAdmin(PermissionAdmin):
    def has_delete_permission(self, request, obj=None):
        return True

    def delete_view(self, request, object_id, extra_context=None):
        if request.method == 'POST':
            client = boto3.client('redshift')
            cluster = Cluster.objects.get(id=object_id)
            client.delete_cluster(ClusterIdentifier=cluster.identifier, SkipFinalClusterSnapshot=True)
        return super().delete_view(request, object_id, extra_context)


@admin.register(Snapshot)
class SnapshotAdmin(PermissionAdmin):
    date_hierarchy = 'create_time'
    search_fields = (
        'create_time_str',
    )
    list_display = (
        '__str__',
        'add_task',
    )
    exclude = (
        'create_time_str',
    )

    @admin.display(description='操作')
    def add_task(self, obj):
        buttons = []

        add_url = reverse('admin:redshift_restoretabletask_add')
        botton1 = f'<a href="{add_url}?snapshot={obj.id}">恢复 表</a>'

        add_url = reverse('admin:redshift_restoreclustertask_add')
        botton2 = f'<a href="{add_url}?snapshot={obj.id}">集群 任务</a>'

        buttons.append(botton1)
        buttons.append(botton2)

        return mark_safe(' / '.join(buttons))

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


@admin.register(RestoreClusterTask)
class RestoreClusterTaskAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        'snapshot',
    )
    list_display = (
        'name',
        'snapshot',
    )
