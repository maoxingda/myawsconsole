# Generated by Django 4.0 on 2023-12-22 07:25

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("schemagenerator", "0010_task_dms_task_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="enable_vue",
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
