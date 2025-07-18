def get_user_profile_instance(user):
	if user.user_type == 'customer' and hasattr(user, 'customerprofile'):
		return user.customerprofile
	elif user.user_type == 'vendor' and hasattr(user, 'vendorprofile'):
		return user.vendorprofile
	elif user.user_type == 'admin' and hasattr(user, 'adminprofile'):
		return user.adminprofile
	return None


def delete_user_and_profile(user):
	"""
	Delete user and their associated profile.
	"""

	profile = get_user_profile_instance(user)
	if profile:
		profile.soft_delete()
	user.soft_delete()


def restore_user_and_profile(user):
	"""
	Restore user and their associated profile.
	"""

	profile = get_user_profile_instance(user)
	if profile:
		profile.restore()
	user.restore()
