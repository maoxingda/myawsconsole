import boto3
from django.conf import settings
from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from common.admin import CommonAdmin
from redshift.models import Snapshot, Table, RestoreTableTask, RestoreClusterTask, Cluster
from redshift.views import refresh_snapshots

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
    list_display = ('identifier', 'html_actions', )

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = []

        cluster_addr = f'{settings.AWS_REDSHIFT_URL}#cluster-details?cluster={obj.identifier.lower()}'
        botton1 = f'<a href="{cluster_addr}">AWS控制台</a>'

        buttons.append(botton1)

        return mark_safe(' / '.join(buttons))

    def has_delete_permission(self, request, obj=None):
        return True

    def delete_view(self, request, object_id, extra_context=None):
        if request.method == 'POST':
            client = boto3.client('redshift')
            cluster = Cluster.objects.get(id=object_id)
            client.delete_cluster(ClusterIdentifier=cluster.identifier, SkipFinalClusterSnapshot=True)
        return super().delete_view(request, object_id, extra_context)

    def delete_queryset(self, request, queryset):
        client = boto3.client('redshift')
        for cluster in queryset:
            client.delete_cluster(ClusterIdentifier=cluster.identifier, SkipFinalClusterSnapshot=True)
        super().delete_queryset(request, queryset)


@admin.register(Snapshot)
class SnapshotAdmin(CommonAdmin):
    date_hierarchy = 'create_time'
    search_fields = ('create_time_str', )
    list_display = ('__str__', 'html_actions', )
    list_display_links = ('__str__', )
    exclude = ('create_time_str', )

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def my_handler(self, request):
        return refresh_snapshots(request)

    def get_exclude(self, request, obj=None):
        exclude = []
        if obj:
            exclude.extend(('start_date', 'end_date', 'create_time_str', ))
        else:
            exclude.extend(('cluster', 'identifier', 'create_time', 'create_time_str', ))
        return exclude

    @admin.display(description='操作')
    def html_actions(self, obj):
        buttons = []

        add_url = reverse('admin:redshift_restoretabletask_add')
        botton1 = f'恢复 <a href="{add_url}?snapshot={obj.id}">【表】</a>'

        add_url = reverse('admin:redshift_restoreclustertask_add')
        botton2 = f'<a href="{add_url}?snapshot={obj.id}">【集群】</a> 任务'

        buttons.append(botton1)
        buttons.append(botton2)

        return mark_safe(' / '.join(buttons))


@admin.register(Table)
class TableAdmin(PermissionAdmin):
    search_fields = ('name', )
    list_filter = ('schema', )


@admin.register(RestoreTableTask)
class RestorTableTaskAdmin(admin.ModelAdmin):
    autocomplete_fields = ('snapshot', )
    list_display = ('name', 'snapshot', 'status', )
    # filter_horizontal = ('tables', )
    exclude = ('status', )


@admin.register(RestoreClusterTask)
class RestoreClusterTaskAdmin(admin.ModelAdmin):
    autocomplete_fields = ('snapshot', )
    list_display = ('name', 'snapshot', 'status', )
    exclude = ('status', )
