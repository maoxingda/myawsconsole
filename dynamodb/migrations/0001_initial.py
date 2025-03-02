# Generated by Django 4.0 on 2024-08-11 23:02

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Order",
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
                ("content", models.JSONField(default=dict, verbose_name="内容")),
            ],
            options={
                "verbose_name": "订单",
                "verbose_name_plural": "订单",
            },
        ),
    ]
