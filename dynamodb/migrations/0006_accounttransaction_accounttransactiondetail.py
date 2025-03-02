# Generated by Django 4.0 on 2024-10-07 13:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("dynamodb", "0005_alter_maintransaction_content_alter_order_content"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccountTransaction",
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
                ("account_rn", models.CharField(max_length=100)),
                ("content", models.JSONField(default=dict)),
            ],
            options={
                "verbose_name": "账户交易",
                "verbose_name_plural": "账户交易",
            },
        ),
        migrations.CreateModel(
            name="AccountTransactionDetail",
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
                ("account_transaction_detail_rn", models.CharField(max_length=100)),
                ("content", models.JSONField(default=dict)),
            ],
            options={
                "verbose_name": "账户交易详情",
                "verbose_name_plural": "账户交易详情",
            },
        ),
    ]
