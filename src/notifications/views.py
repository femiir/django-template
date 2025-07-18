from django.contrib.auth.decorators import login_required
from django.shortcuts import render

# Create your views here.


def dashboard(request):
	"""
	WebSocket Notification Dashboard view.
	Renders the testing interface for WebSocket notifications.
	"""

	return render(request, 'websockets/dashboard.html')

