# Generated by Django 4.1 on 2023-06-19 01:38

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("redshift", "0002_alter_cluster_identifier"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="snapshot",
            unique_together={("cluster", "identifier")},
        ),
    ]
