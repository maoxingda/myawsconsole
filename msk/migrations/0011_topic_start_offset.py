# Generated by Django 4.1 on 2024-10-19 14:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("msk", "0010_remove_topic_is_key_out_of_order"),
    ]

    operations = [
        migrations.AddField(
            model_name="topic",
            name="start_offset",
            field=models.BigIntegerField(
                default=0, editable=False, verbose_name="开始offset"
            ),
        ),
    ]
