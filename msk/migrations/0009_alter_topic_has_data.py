# Generated by Django 4.1 on 2024-10-19 13:15

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("msk", "0008_topic_has_data"),
    ]

    operations = [
        migrations.AlterField(
            model_name="topic",
            name="has_data",
            field=models.BooleanField(
                default=False, editable=False, verbose_name="是否有数据"
            ),
        ),
    ]
