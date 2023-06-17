from django.apps import AppConfig


class SchemageneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'schemagenerator'
    verbose_name = '表结构生成器'
