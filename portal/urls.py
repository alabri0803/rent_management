from django.urls import path
from .views import PortalDashboardView

urlpatterns = [
  path('', PortalDashboardView.as_view(), name='portal_dashboard'),
]