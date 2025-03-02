# Generated by Django 4.0 on 2024-08-12 00:24

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dynamodb", "0003_alter_order_order_rn"),
    ]

    operations = [
        migrations.CreateModel(
            name="MainTransaction",
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
                ("main_transaction_rn", models.CharField(max_length=100)),
                ("content", models.JSONField(default=dict, verbose_name="内容")),
            ],
            options={
                "verbose_name": "主交易",
                "verbose_name_plural": "主交易",
            },
        ),
    ]
