# Generated by Django 4.0 on 2024-05-04 01:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doris', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Table',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=128, verbose_name='表')),
            ],
            options={
                'verbose_name': '表',
                'verbose_name_plural': '表',
                'ordering': ('name',),
            },
        ),
    ]