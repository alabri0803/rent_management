from django.urls import path
from .views import (
    DashboardHomeView, 
    LeaseListView, LeaseDetailView, LeaseCreateView, LeaseUpdateView, LeaseDeleteView, renew_lease, LeaseCancelView,
    DocumentUploadView, DocumentDeleteView,
    MaintenanceRequestAdminListView, MaintenanceRequestAdminUpdateView,
    ExpenseListView, ExpenseCreateView, ExpenseUpdateView, ExpenseDeleteView,
    PaymentListView, PaymentCreateView, PaymentUpdateView, PaymentDeleteView,
    ReportSelectionView, GenerateTenantStatementPDF, GenerateMonthlyPLReportPDF, GenerateAnnualReportPDF, GenerateOccupancyReportPDF, GeneratePaymentReceiptPDF,
    CompanyUpdateView, UpdateTenantRatingView,
)

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='dashboard_home'),
    # Company settings
    path('settings/company/', CompanyUpdateView.as_view(), name='company_update'),
    # Lease management
    path('lease_list', LeaseListView.as_view(), name='lease_list'),
    path('lease/<int:pk>/', LeaseDetailView.as_view(), name='lease_detail'),
    path('lease/new/', LeaseCreateView.as_view(), name='lease_create'),
    path('lease/<int:pk>/edit/', LeaseUpdateView.as_view(), name='lease_update'),
    path('lease/<int:pk>/delete/', LeaseDeleteView.as_view(), name='lease_delete'),
    path('lease/<int:pk>/renew/', renew_lease, name='lease_renew'),
    path('lease/<int:pk>/cancel/', LeaseCancelView.as_view(), name='lease_cancel'),
    # Tenant rating
    path('tenant/<int:pk>/rate/', UpdateTenantRatingView.as_view(), name='tenant_rate'),
    # Document management
    path('lease/<int:lease_pk>/documents/upload/', DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:pk>/delete/', DocumentDeleteView.as_view(), name='document_delete'),
    # Maintenance requests
    path('maintenance/', MaintenanceRequestAdminListView.as_view(), name='maintenance_admin_list'),
    path('maintenance/<int:pk>/', MaintenanceRequestAdminUpdateView.as_view(), name='maintenance_admin_update'),
    # Expenses
    path('expenses/', ExpenseListView.as_view(), name='expense_list'),
    path('expenses/new/', ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<int:pk>/delete/', ExpenseDeleteView.as_view(), name='expense_delete'),
    # Payments
    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payments/new/', PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/edit/', PaymentUpdateView.as_view(), name='payment_update'),
    path('payments/<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'),
    # Reports
    path('reports/', ReportSelectionView.as_view(), name='report_selection'),
    path('reports/tenant/<int:lease_pk>/', GenerateTenantStatementPDF.as_view(), name='report_tenant_statement'),
    path('reports/payment/<int:pk>/receipt', GeneratePaymentReceiptPDF.as_view(), name='report_payment_receipt'),
    path('reports/monthly-pl/', GenerateMonthlyPLReportPDF.as_view(), name='report_monthly_pl'),
    path('reports/annual-pl/', GenerateAnnualReportPDF.as_view(), name='report_annual_pl'),
    path('reports/occupancy/', GenerateOccupancyReportPDF.as_view(), name='report_occupancy'),
]