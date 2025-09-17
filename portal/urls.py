from django.urls import path
from .views import PortalDashboardView, MaintenanceRequestListView, MaintenanceRequestCreateView

urlpatterns = [
    path('', PortalDashboardView.as_view(), name='portal_dashboard'),
    path('maintenance/', MaintenanceRequestListView.as_view(), name='maintenance_list'),
    path('maintenance/new/', MaintenanceRequestCreateView.as_view(), name='maintenance_create'),
]