from django.contrib import admin
from doris import models


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
