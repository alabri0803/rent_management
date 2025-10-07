from django.urls import path
from .views import (
    DashboardHomeView,
    TenantListView, TenantDetailView, TenantCreateView, TenantUpdateView, TenantDeleteView,
    UnitListView, UnitDetailView, UnitCreateView, UnitUpdateView, UnitDeleteView,
    BuildingListView, BuildingCreateView, BuildingUpdateView, BuildingDeleteView,
    LeaseListView, LeaseDetailView, LeaseCreateView, LeaseUpdateView, LeaseDeleteView, renew_lease, LeaseCancelView,
    DocumentUploadView, DocumentDeleteView,
    MaintenanceRequestAdminListView, MaintenanceRequestAdminUpdateView,
    ExpenseListView, ExpenseCreateView, ExpenseUpdateView, ExpenseDeleteView,
    PaymentListView, PaymentCreateView, PaymentUpdateView, PaymentDeleteView, PaymentReceiptPDFView,
    CheckManagementView, CheckStatusUpdateView,
    UserManagementView, UserCreateView, UserUpdateView, UserDeleteView,
    ReportSelectionView, GenerateTenantStatementPDF, GenerateMonthlyPLReportPDF, GenerateAnnualPLReportPDF, GenerateOccupancyReportPDF, GeneratePaymentReceiptPDF,
    CompanyUpdateView, UpdateTenantRatingView,
    InvoiceListView, InvoiceDetailView, InvoiceCreateView, InvoiceUpdateView, InvoiceDeleteView,
)
from .export_views import (
    export_tenants_excel,
    export_leases_excel,
    export_payments_excel,
    export_expenses_excel,
    export_buildings_excel,
    export_units_excel,
    export_maintenance_excel,
)

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='dashboard_home'),

    # Company Settings
    path('settings/company/', CompanyUpdateView.as_view(), name='company_update'),

    # Tenants
    path('tenants/', TenantListView.as_view(), name='tenant_list'),
    path('tenants/<int:pk>/', TenantDetailView.as_view(), name='tenant_detail'),
    path('tenants/new/', TenantCreateView.as_view(), name='tenant_create'),
    path('tenants/<int:pk>/edit/', TenantUpdateView.as_view(), name='tenant_update'),
    path('tenants/<int:pk>/delete/', TenantDeleteView.as_view(), name='tenant_delete'),

    # Units
    path('units/', UnitListView.as_view(), name='unit_list'),
    path('units/<int:pk>/', UnitDetailView.as_view(), name='unit_detail'),
    path('units/new/', UnitCreateView.as_view(), name='unit_create'),
    path('units/<int:pk>/edit/', UnitUpdateView.as_view(), name='unit_update'),
    path('units/<int:pk>/delete/', UnitDeleteView.as_view(), name='unit_delete'),

    # Buildings
    path('buildings/', BuildingListView.as_view(), name='building_list'),
    path('buildings/new/', BuildingCreateView.as_view(), name='building_create'),
    path('buildings/<int:pk>/edit/', BuildingUpdateView.as_view(), name='building_update'),
    path('buildings/<int:pk>/delete/', BuildingDeleteView.as_view(), name='building_delete'),

    # Leases
    path('lease/', LeaseListView.as_view(), name='lease_list'),
    path('lease/<int:pk>/', LeaseDetailView.as_view(), name='lease_detail'),
    path('lease/new/', LeaseCreateView.as_view(), name='lease_create'),
    path('lease/<int:pk>/edit/', LeaseUpdateView.as_view(), name='lease_update'),
    path('lease/<int:pk>/delete/', LeaseDeleteView.as_view(), name='lease_delete'),
    path('lease/<int:pk>/renew/', renew_lease, name='lease_renew'),
    path('lease/<int:pk>/cancel/', LeaseCancelView.as_view(), name='lease_cancel'), # ADDED

    # Tenant Rating - ADDED
    path('tenant/<int:pk>/rate/', UpdateTenantRatingView.as_view(), name='tenant_rate'),

    # Documents
    path('lease/<int:lease_pk>/documents/upload/', DocumentUploadView.as_view(), name='document_upload'),
    path('documents/<int:pk>/delete/', DocumentDeleteView.as_view(), name='document_delete'),

    # Maintenance
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
    path('payments/<int:pk>/delete/', PaymentDeleteView.as_view(), name='payment_delete'), # ADDED
    path('payments/<int:pk>/receipt/', PaymentReceiptPDFView.as_view(), name='payment_receipt'),
    
    # Check Management
    path('checks/', CheckManagementView.as_view(), name='check_management'),
    path('checks/<int:pk>/update-status/', CheckStatusUpdateView.as_view(), name='check_status_update'),
    
    # User Management
    path('users/', UserManagementView.as_view(), name='user_management'),
    path('users/new/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/edit/', UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user_delete'),

    # Reports
    path('reports/', ReportSelectionView.as_view(), name='report_selection'),
    path('reports/tenant/<int:lease_pk>/', GenerateTenantStatementPDF.as_view(), name='report_tenant_statement'),
    path('reports/payment/<int:pk>/receipt/', GeneratePaymentReceiptPDF.as_view(), name='report_payment_receipt'), # ADDED
    path('reports/monthly-pl/', GenerateMonthlyPLReportPDF.as_view(), name='report_monthly_pl'),
    path('reports/annual-pl/', GenerateAnnualPLReportPDF.as_view(), name='report_annual_pl'), # ADDED
    path('reports/occupancy/', GenerateOccupancyReportPDF.as_view(), name='report_occupancy'), # ADDED
    
    # Excel Exports
    path('export/tenants/', export_tenants_excel, name='export_tenants_excel'),
    path('export/leases/', export_leases_excel, name='export_leases_excel'),
    path('export/payments/', export_payments_excel, name='export_payments_excel'),
    path('export/expenses/', export_expenses_excel, name='export_expenses_excel'),
    path('export/buildings/', export_buildings_excel, name='export_buildings_excel'),
    path('export/units/', export_units_excel, name='export_units_excel'),
    path('export/maintenance/', export_maintenance_excel, name='export_maintenance_excel'),

    # Invoices
    path('invoices/', InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/new/', InvoiceCreateView.as_view(), name='invoice_create'),
    path('invoices/<int:pk>/edit/', InvoiceUpdateView.as_view(), name='invoice_update'),
    path('invoices/<int:pk>/delete/', InvoiceDeleteView.as_view(), name='invoice_delete'),
]