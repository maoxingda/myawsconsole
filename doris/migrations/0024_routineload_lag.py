# Generated by Django 4.1 on 2024-10-12 03:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("doris", "0023_alter_routineload_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="routineload",
            name="lag",
            field=models.BigIntegerField(default=0, verbose_name="延迟"),
        ),
    ]
