import boto3
from django.contrib import admin

from redshift.models import Snapshot, Table, RestoreTableTask, RestoreClusterTask, Cluster


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
        '__str__',  # TODO 从快照列表页添加创建：恢复表、集群任务快捷键
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


@admin.register(RestoreClusterTask)
class RestoreClusterTaskAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        'snapshot',
    )
    list_display = (
        'name',
        'snapshot',
    )
