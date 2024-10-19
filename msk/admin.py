from django.contrib import admin
from msk import models


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = (
        'name',
    )
    search_fields = (
        'name',
    )
    readonly_fields = (
        'html_actions',
    )
