# Generated by Django 4.0 on 2024-07-10 05:37

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("doris", "0022_alter_routineload_name_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="routineload",
            options={
                "ordering": ("db", "name"),
                "verbose_name": "例行加载任务",
                "verbose_name_plural": "例行加载任务",
            },
        ),
    ]
