# Generated by Django 5.2.1 on 2025-06-09 11:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_vendorprofile_nickname'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendorprofile',
            name='nickname',
        ),
    ]
