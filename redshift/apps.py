from django.apps import AppConfig


class RedshiftConfig(AppConfig):
    def ready(self):
        super().ready()
        from redshift.models import Snapshot
        from datetime import datetime, timedelta
        Snapshot.objects.filter(create_time__lte=datetime.utcnow() - timedelta(days=35)).delete()  # redshift集群快照最多能保留35天

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'redshift'
    verbose_name = '离线数仓'
