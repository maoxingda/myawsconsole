from django.contrib import admin
from doris import models

from admin_extra_buttons.api import ExtraButtonsMixin, button

from . import views


@admin.register(models.S3LoadTask)
class S3LoadTaskAdmin(admin.ModelAdmin):
    readonly_fields = (
        'html_actions',
        'attempts',
    )
    radio_fields = {
        'type': admin.HORIZONTAL,
    }
    autocomplete_fields = (
        'table',
    )


@admin.register(models.Table)
class TableAdmin(admin.ModelAdmin):
    search_fields = (
        'name',
    )
    list_display = (
        'html_actions',
        'name',
    )


@admin.register(models.RoutineLoad)
class RoutineLoadAdmin(ExtraButtonsMixin):
    search_fields = (
        'name',
    )
    list_display = (
        '__str__',
        'lag',
        'state',
    )
    list_filter = (
        'state',
        'lag',
    )
    readonly_fields = (
        'html_actions',
    )
    actions = (
        'batch_pause_routine_load',
        'batch_resume_routine_load',
        'batch_stop_routine_load',
        'batch_recreate_routine_load',
        'batch_print_routine_load',
    )

    @button(label='刷新列表')
    def refresh_routine_load_changelist(self, request):
        views.routineload_refresh(request)

    @button(label='刷新数据库')
    def refresh_databases(self, request):
        views.refresh_doris_db(request)

    @admin.display(description='暂停所选的 例行加载任务')
    def batch_pause_routine_load(self, _, queryset):
        from doris.views import pause_routine_load
        for routine_load in queryset:
            pause_routine_load(routine_load)

    @admin.display(description='恢复所选的 例行加载任务')
    def batch_resume_routine_load(self, _, queryset):
        from doris.views import resume_routine_load
        for routine_load in queryset:
            resume_routine_load(routine_load)

    @admin.display(description='重建所选的 例行加载任务')
    def batch_recreate_routine_load(self, _, queryset):
        from doris.views import recreate_routine_load
        for routine_load in queryset:
            recreate_routine_load(routine_load)

    @admin.display(description='停止所选的 例行加载任务')
    def batch_stop_routine_load(self, _, queryset):
        from doris.views import stop_routine_load
        for routine_load in queryset:
            stop_routine_load(routine_load)

    @admin.display(description='打印所选的 例行加载任务')
    def batch_print_routine_load(self, _, queryset):
        from doris.views import print_routine_load
        sqls = []
        for routine_load in queryset:
            sqls.append(f'use {routine_load.db.name};')
            sqls.append(print_routine_load(routine_load))
        with open('/tmp/routine_load.sql', 'w') as f:
            f.write('\n'.join(sqls))

        print(f'scp pdaf:/tmp/routine_load.sql /tmp/routine_load.sql && goland /tmp/routine_load.sql')

