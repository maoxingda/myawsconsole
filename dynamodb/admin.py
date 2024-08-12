from django.contrib import admin
from dynamodb import models


class DisableAddChangePermAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(models.Order)
class OrderAdmin(DisableAddChangePermAdmin):
    list_display = (
        'order_rn',
        'content_format',
    )
    search_fields = (
        'order_rn',
    )


@admin.register(models.MainTransaction)
class MainTransactionAdmin(DisableAddChangePermAdmin):
    list_display = (
        'main_transaction_rn',
        'content_format',
    )
    search_fields = (
        'main_transaction_rn',
    )