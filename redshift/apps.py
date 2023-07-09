from django.apps import AppConfig


class RedshiftConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'redshift'
    verbose_name = '离线数仓'
