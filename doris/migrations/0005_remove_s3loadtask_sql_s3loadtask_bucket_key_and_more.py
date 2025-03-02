# Generated by Django 4.0 on 2024-05-04 02:17

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("doris", "0004_alter_s3loadtask_type"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="s3loadtask",
            name="sql",
        ),
        migrations.AddField(
            model_name="s3loadtask",
            name="bucket_key",
            field=models.CharField(
                default=django.utils.timezone.now, max_length=256, verbose_name="分桶键"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="s3loadtask",
            name="sort_key",
            field=models.CharField(
                default=django.utils.timezone.now, max_length=256, verbose_name="排序键"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="s3loadtask",
            name="table",
            field=models.ForeignKey(
                default=1, on_delete=django.db.models.deletion.CASCADE, to="doris.table"
            ),
            preserve_default=False,
        ),
    ]
