# Generated by Django 4.1 on 2025-02-26 04:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("redshift", "0008_queryhistory"),
    ]

    operations = [
        migrations.AlterField(
            model_name="queryhistory",
            name="elapsed",
            field=models.BigIntegerField(help_text="单位：分钟", verbose_name="耗时"),
        ),
    ]
