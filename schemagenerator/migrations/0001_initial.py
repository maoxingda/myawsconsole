# Generated by Django 4.1 on 2023-06-17 13:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DbConn",
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
                    models.CharField(
                        max_length=128, unique=True, verbose_name="数据库"
                    ),
                ),
                (
                    "db_type",
                    models.CharField(
                        choices=[("mysql", "MySQL"), ("postgres", "PostgreSQL")],
                        default="postgres",
                        max_length=16,
                        verbose_name="类型",
                    ),
                ),
                ("dns", models.CharField(max_length=256, verbose_name="地址")),
                ("port", models.SmallIntegerField(default=5432, verbose_name="端口号")),
                ("user", models.CharField(max_length=256, verbose_name="用户")),
                ("password", models.CharField(max_length=256, verbose_name="密码")),
                (
                    "schema",
                    models.CharField(
                        default="public", max_length=128, verbose_name="源表Schema"
                    ),
                ),
                (
                    "target_schema",
                    models.CharField(
                        blank=True,
                        default="temp",
                        help_text="可选参数 默认为：temp",
                        max_length=128,
                        verbose_name="目标表Schema",
                    ),
                ),
                (
                    "target_table_name_prefix",
                    models.CharField(
                        blank=True,
                        help_text="可选参数 默认为：数据库 + _",
                        max_length=128,
                        verbose_name="目标表前缀",
                    ),
                ),
                (
                    "s3_path",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="外部表Location",
                    ),
                ),
            ],
            options={
                "verbose_name": "数据库连接",
                "verbose_name_plural": "数据库连接",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="Table",
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
                ("name", models.CharField(max_length=128, verbose_name="表")),
                (
                    "conn",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="db_tables",
                        to="schemagenerator.dbconn",
                        verbose_name="数据库地址",
                    ),
                ),
            ],
            options={
                "verbose_name": "表",
                "verbose_name_plural": "表",
                "ordering": ("conn", "name"),
                "unique_together": {("conn", "name")},
            },
        ),
        migrations.CreateModel(
            name="Task",
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
                ("name", models.CharField(max_length=128, verbose_name="名称")),
                (
                    "status",
                    models.CharField(
                        default="CREATED", max_length=32, verbose_name="状态"
                    ),
                ),
                (
                    "conn",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tasks",
                        to="schemagenerator.dbconn",
                        verbose_name="数据库",
                    ),
                ),
            ],
            options={
                "verbose_name": "任务",
                "verbose_name_plural": "任务",
                "ordering": ("name",),
            },
        ),
        migrations.CreateModel(
            name="TaskTable",
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
                    "table",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="task_tables",
                        to="schemagenerator.table",
                        verbose_name="表",
                    ),
                ),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sync_tables",
                        to="schemagenerator.task",
                        verbose_name="任务",
                    ),
                ),
            ],
            options={
                "verbose_name": "表",
                "verbose_name_plural": "表",
            },
        ),
    ]
