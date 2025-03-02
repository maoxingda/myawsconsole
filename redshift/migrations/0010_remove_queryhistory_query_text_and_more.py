# Generated by Django 4.1 on 2025-02-26 15:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("redshift", "0009_alter_queryhistory_elapsed"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="queryhistory",
            name="query_text",
        ),
        migrations.AddField(
            model_name="queryhistory",
            name="dashboard_code",
            field=models.CharField(max_length=16, null=True, verbose_name="报表编码"),
        ),
        migrations.AddField(
            model_name="queryhistory",
            name="query_uuid",
            field=models.CharField(max_length=64, null=True, verbose_name="查询UUID"),
        ),
    ]
