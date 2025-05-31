from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AdminProfile, CustomerProfile, User, UserType, VendorProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
	if not created:
		return

	if instance.user_type == UserType.VENDOR:
		VendorProfile.objects.get_or_create(user=instance)
	elif instance.user_type == UserType.CUSTOMER:
		CustomerProfile.objects.get_or_create(user=instance)
	elif instance.user_type == UserType.ADMIN:
		AdminProfile.objects.get_or_create(user=instance)
