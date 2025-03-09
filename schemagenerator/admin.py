import os
import urllib

from django.contrib import admin

from schemagenerator.models import DbConn, Table, Task, TaskTable


def get_search_results_ajax(queryset, key, urlparams):
    db_conn_id = urlparams.get("db_conn_id", [0])
    if (
        isinstance(key, str)
        and key.startswith("id_sync_tables-")
        and isinstance(db_conn_id, list)
        and db_conn_id[0] != "null"
    ):
        return queryset.filter(conn=db_conn_id[0])
    return queryset


class AjaxModelAdmin(admin.ModelAdmin):
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        if "/autocomplete/" in request.path and request.headers.get("x-requested-with") == "XMLHttpRequest":
            url = urllib.parse.urlparse(request.headers["Referer"])
            urlparams = urllib.parse.parse_qs(url.query)
            key = urlparams.get("key")
            if type(key) in (list, tuple):
                key = key[0]
            queryset = get_search_results_ajax(queryset, key, urlparams)
        return queryset, use_distinct


@admin.register(DbConn)
class DbConnAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = (
        "name",
        "html_actions",
    )
    radio_fields = {
        "db_type": admin.HORIZONTAL,
    }
    view_on_site = False

    def save_model(self, request, obj: DbConn, form, change):
        import pwd

        if pwd.getpwuid(os.getuid())[0] != "ec2-user":
            obj.s3_path = f"s3://bi-data-store/realtime-cdc/{obj.name}/{obj.schema}/"
        else:
            obj.s3_path = f"s3://bi-data-lake/realtime-cdc/{obj.name}/{obj.schema}/"

        super().save_model(request, obj, form, change)


@admin.register(Table)
class TableAdmin(AjaxModelAdmin):
    search_fields = ("name",)
    list_display = (
        "name",
        "conn",
    )
    list_filter = ("conn",)

    def has_change_permission(self, request, obj=None):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_add_permission(self, request):
        return False


class TaskTableInlineAdmin(admin.TabularInline):
    extra = 0
    model = TaskTable
    autocomplete_fields = ("table",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    inlines = (TaskTableInlineAdmin,)
    list_display = (
        "name",
        "status",
        "conn",
    )
    autocomplete_fields = ("conn",)
    readonly_fields = (
        "status",
        "html_actions",
    )
    radio_fields = {
        "task_type": admin.HORIZONTAL,
    }
    view_on_site = False
