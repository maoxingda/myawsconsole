# Generated by Django 4.1 on 2025-02-21 06:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0007_alter_replicationtask_replication_task_stats'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReplicationEndpoint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint_arn', models.CharField(max_length=255)),
                ('endpoint_identifier', models.CharField(max_length=255, unique=True)),
                ('endpoint_type', models.CharField(max_length=50)),
                ('engine_name', models.CharField(max_length=50)),
                ('engine_display_name', models.CharField(max_length=50)),
                ('status', models.CharField(max_length=50)),
                ('database_name', models.CharField(max_length=50)),
                ('server_name', models.CharField(max_length=50)),
            ],
            options={
                'verbose_name': '端点v2',
                'verbose_name_plural': '端点v2',
            },
        ),
    ]
