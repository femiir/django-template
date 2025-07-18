from django.contrib import admin
from .models import NotificationPreference, Notification

# Register your models here.
admin.site.register(NotificationPreference)
admin.site.register(Notification)
