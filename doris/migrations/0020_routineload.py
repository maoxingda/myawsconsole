# Generated by Django 4.0 on 2024-07-10 04:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("doris", "0019_s3loadtask_is_load_data_s3loadtask_is_unload_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="RoutineLoad",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=32, unique=True, verbose_name="名称"),
                ),
                (
                    "db",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="doris.dorisdb",
                        verbose_name="数据库",
                    ),
                ),
            ],
            options={
                "verbose_name": "例行加载任务",
                "verbose_name_plural": "例行加载任务",
            },
        ),
    ]
