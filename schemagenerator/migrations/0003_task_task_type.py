# Generated by Django 4.1 on 2023-07-07 14:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("schemagenerator", "0002_alter_task_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="task_type",
            field=models.CharField(
                default="schema", max_length=32, verbose_name="任务类型"
            ),
        ),
    ]
