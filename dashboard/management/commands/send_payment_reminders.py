from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from dashboard.models import Lease, Notification

class Command(BaseCommand):
    help = 'Send notifications for upcoming and overdue payments'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        active_leases = Lease.objects.filter(status__in=['active', 'expiring_soon'])
        for lease in active_leases:
          self.stdout.write(self.style.SUCCESS(f'Checking lease {lease.contract_number}'))
        self.stdout.write(self.style.SUCCESS('Payment reminders process finished.'))