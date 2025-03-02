# Generated by Django 4.1 on 2023-06-19 01:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dms", "0002_table_task_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="table",
            name="name",
            field=models.CharField(max_length=255, verbose_name="名称"),
        ),
        migrations.AlterField(
            model_name="table",
            name="task_name",
            field=models.CharField(max_length=255, null=True, verbose_name="任务名称"),
        ),
        migrations.AlterUniqueTogether(
            name="table",
            unique_together={("task_name", "name")},
        ),
    ]
