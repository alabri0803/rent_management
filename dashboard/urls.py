from django.urls import path
from .views import LeaseListView, LeaseDetailView, LeaseCreateView, LeaseUpdateView, LeaseDeleteView, renew_lease, MaintenanceRequestAdminListView, MaintenanceRequestAdminUpdateView, DocumentUploadView, DocumentDeleteView

urlpatterns = [
  path('', LeaseListView.as_view(), name='lease_list'),
  path('leases/<int:pk>/', LeaseDetailView.as_view(), name='lease_detail'),
  path('leases/new/', LeaseCreateView.as_view(), name='lease_create'),
  path('leases/<int:pk>/edit/', LeaseUpdateView.as_view(), name='lease_update'),
  path('leases/<int:pk>/delete/', LeaseDeleteView.as_view(), name='lease_delete'),
  path('leases/<int:pk>/renew/', renew_lease, name='renew_lease'),
  path('maintenance/', MaintenanceRequestAdminListView.as_view(), name='maintenance_admin_list'),
  path('maintenance/<int:pk>/', MaintenanceRequestAdminUpdateView.as_view(), name='maintenance_admin_update'),
  path('leases/<int:lease_pk>/documents/upload/', DocumentUploadView.as_view(), name='document_upload'),
  path('documents/<int:pk>/delete/', DocumentDeleteView.as_view(), name='document_delete'),
]