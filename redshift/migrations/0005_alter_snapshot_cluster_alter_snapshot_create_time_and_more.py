# Generated by Django 4.1 on 2023-07-01 00:19

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("redshift", "0004_restoretabletask_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="snapshot",
            name="cluster",
            field=models.CharField(editable=False, max_length=128, verbose_name="集群"),
        ),
        migrations.AlterField(
            model_name="snapshot",
            name="create_time",
            field=models.DateTimeField(editable=False, verbose_name="创建时间"),
        ),
        migrations.AlterField(
            model_name="snapshot",
            name="identifier",
            field=models.CharField(editable=False, max_length=128, verbose_name="快照"),
        ),
    ]
