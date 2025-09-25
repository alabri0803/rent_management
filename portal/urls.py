from django.urls import path
from .views import PortalDashboardView, MaintenanceRequestListView, MaintenanceRequestCreateView, NotificationListView, mark_notification_as_read

urlpatterns = [
    path('', PortalDashboardView.as_view(), name='portal_dashboard'),
    path('maintenance/', MaintenanceRequestListView.as_view(), name='maintenance_list'),
    path('maintenance/new/', MaintenanceRequestCreateView.as_view(), name='maintenance_create'),
    path('notifications/', NotificationListView.as_view(), name='notification_list'),
    path('notifications/mark-read/<int:pk>/', mark_notification_as_read, name='notification_mark_read'),
]