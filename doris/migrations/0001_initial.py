# Generated by Django 4.0 on 2024-05-04 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='S3LoadTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sql', models.TextField(verbose_name='SQL')),
            ],
            options={
                'verbose_name': 'S3 LOAD',
                'verbose_name_plural': 'S3 LOAD',
            },
        ),
    ]