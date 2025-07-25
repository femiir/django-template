# Generated by Django 5.2.1 on 2025-07-05 05:47

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('message', models.TextField(blank=True, null=True)),
                ('read', models.BooleanField(default=False)),
                ('source_app', models.CharField(blank=True, max_length=100, null=True)),
                ('verb', models.CharField(choices=[('like', 'Like'), ('comment', 'Comment'), ('follow', 'Follow'), ('mention', 'Mention'), ('share', 'Share'), ('other', 'Other'), ('report', 'Report'), ('issue', 'Issue'), ('resolved', 'Resolved')], default='other', max_length=255)),
                ('actor_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('target_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('actor_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype')),
                ('target_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='contenttypes.contenttype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'db_table': 'notifications_table',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='NotificationChannel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('channel_type', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('push', 'Push'), ('in_app', 'In-App')], default='email', max_length=50)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('failed', 'Failed')], default='pending', max_length=50)),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='channels', to='notifications.notification')),
            ],
            options={
                'verbose_name': 'Notification Channel',
                'verbose_name_plural': 'Notification Channels',
                'db_table': 'notification_channels_table',
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('email', models.BooleanField(default=True)),
                ('sms', models.BooleanField(default=False)),
                ('push', models.BooleanField(default=False)),
                ('in_app', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
