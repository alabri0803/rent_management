from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from dashboard.models import Lease, Payment, Expense, MaintenanceRequest, Tenant, Building, Document

class Command(BaseCommand):
  help = 'Creates default user rols (Group) and assigns default permissions.'

  def handle(self, *args, **kwargs):
    self.stdout.write(self.style.SUCCESS('Starting roles and permissions setup...'))

    staff_group, created_staff = Group.objects.get_or_create(name='staff')
    tenant_group, created_tenant = Group.objects.get_or_create(name='tenant')

    if created_staff:
      self.stdout.write('Group "staff" created.')
    if created_tenant:
      self.stdout.write('Group "tenant" created.')

    MODELS_PERMISSIONS = {
      Lease: ['view', 'add', 'change'],
      Payment: ['view', 'add', 'change'],
      Expense: ['view', 'add', 'change'],
      MaintenanceRequest: ['view', 'change'],
      Tenant: ['view'],
      Building: ['view'],
      Document: ['view', 'add', 'delete'],
    }
    staff_group.permissions.clear()
    for model, perms in MODELS_PERMISSIONS.items():
      content_type = ContentType.objects.get_for_model(model)
      for perm_codename in perms:
        try:
          permission = Permission.objects.get(
            content_type=content_type, 
            codename=f"{perm_codename}_{model._meta.model_name}"
          )
          staff_group.permissions.add(permission)
          self.stdout.write(f'  - Assigning {permission.codename} to staff group.')
        except Permission.DoesNotExist:
          self.stdout.write(self.style.ERROR(f'  - Permission {perm_codename}_{model._meta.model_name} not found.'))
    self.stdout.write(self.style.SUCCESS('Successfully set up default roles and permissions.'))