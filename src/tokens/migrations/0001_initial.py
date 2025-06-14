# Generated by Django 5.2.1 on 2025-06-02 05:26

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TrackedToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('jti', models.CharField(max_length=255, unique=True)),
                ('exp', models.DateTimeField()),
                ('token', models.TextField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tracked_models', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Tracked Token',
                'verbose_name_plural': 'Tracked Tokens',
                'db_table': 'tracked_tokens',
                'ordering': ['-created_at'],
                'unique_together': {('user', 'jti')},
            },
        ),
        migrations.CreateModel(
            name='BlacklistedToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('blacklisted_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blacklisted_tokens', to=settings.AUTH_USER_MODEL)),
                ('token', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='blacklisted_token', to='tokens.trackedtoken')),
            ],
            options={
                'verbose_name': 'Blacklisted Token',
                'verbose_name_plural': 'Blacklisted Tokens',
                'db_table': 'blacklisted_tokens',
                'ordering': ['-created_at'],
            },
        ),
    ]
