# Generated by Django 4.1 on 2023-06-19 01:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dms", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="table",
            name="task_name",
            field=models.CharField(max_length=255, null=True, verbose_name="任务m名称"),
        ),
    ]
