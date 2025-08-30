from django.core.management.base import BaseCommand
from dashboard.models import Lease
from django.utils.translation import gettext_lazy as _

class Command(BaseCommand):
  help = 'Updates the status of all leases based on their end dates'
  def handle(self, *args, **kwargs):
    self.stdout.write(self.style.SUCCESS(_('Starting lease status update process...')))
    updated_count = 0
    leases_to_check = Lease.objects.exclude(status__in=['expired', 'cancelled'])
    for lease in leases_to_check:
      original_status = lease.status
      lease.update_status()
      if lease.status != original_status:
        lease.save()
        updated_count += 1
        self.stdout.write(self.style.SUCCESS(_('Processed finished. Updated %(count)d leases.')% {'count': updated_count}))