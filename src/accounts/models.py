from django.db import models
from common.base_model import TimeStampedSoftDeleteModel
from common.manager import CustomUserManager, UserTypeManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


# Create your models here.
class UserType(models.TextChoices):
    VENDOR = "vendor", "Vendor"
    CUSTOMER = "customer", "Customer"
    ADMIN = "admin", "Admin"


class User(AbstractBaseUser, PermissionsMixin, TimeStampedSoftDeleteModel):
    email = models.EmailField(unique=True)
    user_type = models.CharField(
        max_length=20, choices=UserType.choices, default=UserType.CUSTOMER
    )
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Vendor(User):
    objects = UserTypeManager(user_type=UserType.VENDOR)

    class Meta:
        proxy = True
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"

    @property
    def profile(self):
        return getattr(self, "vendorprofile", None)

    def save(self, *args, **kwargs):
        self.user_type = UserType.VENDOR
        super().save(*args, **kwargs)


class Customer(User):
    objects = UserTypeManager(user_type=UserType.CUSTOMER)

    class Meta:
        proxy = True
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    @property
    def profile(self):
        return getattr(self, "customerprofile", None)

    def save(self, *args, **kwargs):
        self.user_type = UserType.CUSTOMER
        super().save(*args, **kwargs)


class Admin(User):
    objects = UserTypeManager(user_type=UserType.ADMIN)

    class Meta:
        proxy = True
        verbose_name = "Admin"
        verbose_name_plural = "Admins"

    @property
    def profile(self):
        return getattr(self, "adminprofile", None)

    def save(self, *args, **kwargs):
        self.user_type = UserType.ADMIN
        super().save(*args, **kwargs)


class VendorProfile(TimeStampedSoftDeleteModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="vendorprofile"
    )

    def __str__(self):
        return self.user.email


class CustomerProfile(TimeStampedSoftDeleteModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="customerprofile"
    )

    def __str__(self):
        return self.user.email


class AdminProfile(TimeStampedSoftDeleteModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="adminprofile"
    )

    def __str__(self):
        return self.user.email
