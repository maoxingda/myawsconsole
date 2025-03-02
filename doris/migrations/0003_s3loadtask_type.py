# Generated by Django 4.0 on 2024-05-04 02:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("doris", "0002_table"),
    ]

    operations = [
        migrations.AddField(
            model_name="s3loadtask",
            name="type",
            field=models.CharField(
                choices=[("a", "聚合模型"), ("d", "明细模型"), ("u", "主键模型")],
                default="d",
                max_length=1,
                verbose_name="模型",
            ),
        ),
    ]
