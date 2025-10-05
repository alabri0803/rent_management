from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from dashboard.models import Lease, Notification
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Send automatic notifications for late payments and lease renewals'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        created_count = 0
        
        # Create notifications for late payments (3 months)
        for lease in Lease.objects.filter(status__in=['active', 'expiring_soon']):
            summary = lease.get_payment_summary()
            unpaid_months = [m for m in summary if m['status'] == 'due' and m['balance'] > 0]
            if len(unpaid_months) >= 3:
                user = lease.tenant.user if hasattr(lease.tenant, 'user') else User.objects.filter(is_staff=True).first()
                if user:
                    obj, created = Notification.objects.get_or_create(
                        user=user,
                        message=f'إنذار: تأخر في سداد الإيجار لعقد {lease.contract_number} لمدة {len(unpaid_months)} شهر',
                        defaults={'read': False}
                    )
                    if created:
                        created_count += 1

        # Create notifications for lease renewal (1 month before expiry)
        one_month_later = today + relativedelta(months=1)
        for lease in Lease.objects.filter(end_date__lte=one_month_later, end_date__gte=today, status='expiring_soon'):
            user = lease.tenant.user if hasattr(lease.tenant, 'user') else User.objects.filter(is_staff=True).first()
            if user:
                obj, created = Notification.objects.get_or_create(
                    user=user,
                    message=f'هل لديك رغبة في تجديد عقد الإيجار رقم {lease.contract_number}؟ ينتهي في {lease.end_date.strftime("%d/%m/%Y")}',
                    defaults={'read': False}
                )
                if created:
                    created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} notifications'))
