# Generated by Django 4.1 on 2023-06-14 00:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0008_alter_endpoint_database'),
    ]

    operations = [
        migrations.AddField(
            model_name='endpoint',
            name='database_addr',
            field=models.CharField(max_length=32, null=True, verbose_name='数据库地址'),
        ),
    ]