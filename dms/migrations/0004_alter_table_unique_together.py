# Generated by Django 4.1 on 2023-06-25 10:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dms', '0003_alter_table_name_alter_table_task_name_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='table',
            unique_together={('task_name', 'schema', 'name')},
        ),
    ]
