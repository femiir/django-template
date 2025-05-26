from django.contrib import admin
from .models import User, Vendor, Customer
from .models import Admin, VendorProfile, CustomerProfile, AdminProfile


# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "user_type", "is_active", "is_staff", "date_joined")
    search_fields = ("email",)
    list_filter = ("user_type", "is_active", "is_staff")
    ordering = ("-date_joined",)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("email", "user_type", "is_active", "is_staff", "date_joined")
    search_fields = ("email",)
    list_filter = ("user_type", "is_active", "is_staff")
    ordering = ("-date_joined",)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("email", "user_type", "is_active", "is_staff", "date_joined")
    search_fields = ("email",)
    list_filter = ("user_type", "is_active", "is_staff")
    ordering = ("-date_joined",)


@admin.register(Admin)
class AdminAdmin(admin.ModelAdmin):
    list_display = ("email", "user_type", "is_active", "is_staff", "date_joined")
    search_fields = ("email",)
    list_filter = ("user_type", "is_active", "is_staff")
    ordering = ("-date_joined",)


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__email",)
    list_filter = ("created_at",)
    ordering = ("-created_at",)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__email",)
    list_filter = ("created_at",)
    ordering = ("-created_at",)


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    search_fields = ("user__email",)
    list_filter = ("created_at",)
    ordering = ("-created_at",)


# admin.site.register(User, UserAdmin)
# admin.site.register(Vendor, VendorAdmin)
# admin.site.register(Customer, CustomerAdmin)
# admin.site.register(Admin, AdminAdmin)
# admin.site.register(VendorProfile, VendorProfileAdmin)
# admin.site.register(CustomerProfile, CustomerProfileAdmin)
# admin.site.register(AdminProfile, AdminProfileAdmin)
