# accounts/manager.py
from django.db import models
from django.contrib.auth.models import BaseUserManager


class UserTypeManager(models.Manager):
    def __init__(self, user_type=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_type = user_type

    def get_queryset(self):
        qs = super().get_queryset()
        if self.user_type:
            return qs.filter(user_type=self.user_type)
        return qs


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", False)
        return self.create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)
    