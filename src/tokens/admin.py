from django.contrib import admin

from .models import BlacklistedToken, TrackedToken


@admin.register(TrackedToken)
class TrackedTokenAdmin(admin.ModelAdmin):
	list_display = ('user', 'refresh_token', 'created_at', 'modified')
	search_fields = ('user__email',)
	list_filter = ('created_at', 'modified')

	def get_queryset(self, request):
		return self.model.all_objects.all()


@admin.register(BlacklistedToken)
class BlacklistedTokenAdmin(admin.ModelAdmin):
	list_display = ('user', 'token', 'created_at', 'modified')
	search_fields = ('user__email',)
	list_filter = ('created_at', 'modified')

	def get_queryset(self, request):
		return self.model.all_objects.all()
