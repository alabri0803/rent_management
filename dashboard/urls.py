from django.urls import path
from .views import (
    LeaseListView, LeaseDetailView, LeaseCreateView, LeaseUpdateView, LeaseDeleteView, renew_lease,
    DocumentUploadView, DocumentDeleteView,
    MaintenanceRequestAdminListView, MaintenanceRequestAdminUpdateView,
    ExpenseListView, ExpenseCreateView, ExpenseUpdateView, ExpenseDeleteView,
    ReportSelectionView, GenerateTenantStatementPDF, GenerateMonthlyPLReportPDF, PaymentCreateView, PaymentUpdateView, PaymentListView, DashboardHomeView, cancel_lease, GeneratePaymentVoucherPDF, GenerateDisbursementVoucherPDF, GenerateLeaseCancellationPDF, export_payments_to_excel
)

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='dashboard_home'),
    path('lease_list', LeaseListView.as_view(), name='lease_list'),
    path('lease/<int:pk>/', LeaseDetailView.as_view(), name='lease_detail'),
    path('lease/new/', LeaseCreateView.as_view(), name='lease_create'),
    path('lease/<int:pk>/edit/', LeaseUpdateView.as_view(), name='lease_update'),
    path('lease/<int:pk>/delete/', LeaseDeleteView.as_view(), name='lease_delete'),
    path('lease/<int:pk>/renew/', renew_lease, name='lease_renew'),
    path('lease/<int:lease_pk>/documents/upload/', DocumentUploadView.as_view(), name='document_upload'),
    path('lease/<int:pk>/cancel/', cancel_lease, name='lease_cancel'),
    path('documents/<int:pk>/delete/', DocumentDeleteView.as_view(), name='document_delete'),
    path('maintenance/', MaintenanceRequestAdminListView.as_view(), name='maintenance_admin_list'),
    path('maintenance/<int:pk>/', MaintenanceRequestAdminUpdateView.as_view(), name='maintenance_admin_update'),
    path('expenses/', ExpenseListView.as_view(), name='expense_list'),
    path('expenses/new/', ExpenseCreateView.as_view(), name='expense_create'),
    path('expenses/<int:pk>/edit/', ExpenseUpdateView.as_view(), name='expense_update'),
    path('expenses/<int:pk>/delete/', ExpenseDeleteView.as_view(), name='expense_delete'),
    path('payments/', PaymentListView.as_view(), name='payment_list'),
    path('payments/new/', PaymentCreateView.as_view(), name='payment_create'),
    path('payments/<int:pk>/edit/', PaymentUpdateView.as_view(), name='payment_update'),
    path('reports/', ReportSelectionView.as_view(), name='report_selection'),
    path('reports/tenant/<int:lease_pk>/', GenerateTenantStatementPDF.as_view(), name='report_tenant_statement'),
    path('reports/monthly-pl/', GenerateMonthlyPLReportPDF.as_view(), name='report_monthly_pl'),
    path('reports/lease/<int:lease_pk>/cancellation-form/', GenerateLeaseCancellationPDF.as_view(), name='report_lease_cancellation'),
    path('reports/payment/<int:payment_pk>/voucher/', GeneratePaymentVoucherPDF.as_view(), name='report_payment_voucher'),
    path('reports/expense/<int:expense_pk>/voucher/', GenerateDisbursementVoucherPDF.as_view(), name='report_disbursement_voucher'),
    path('payment/export/excel/', export_payments_to_excel, name='export_payments_excel'),
]