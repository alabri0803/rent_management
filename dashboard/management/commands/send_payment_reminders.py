from django.core.management.base import BaseCommand
from django.utils import timezone
from  dateutil.relativedelta import relativedelta
from django.utils.translation import gettext as _
from dashboard.models import Lease, Notification, User
from django.db.models import Sum

class Command(BaseCommand):
  help = 'Sends notifications for upcoming and overdue rent payments.'
  def handle(self, *args, **kwargs):
    today = timezone.now().date()
    staff_users = User.objects.filter(is_staff=True)
    self.stdout.write(self.style.SUCCESS(_('Starting payment reminders process...')))
    active_leases = Lease.objects.filter(status__in=['active', 'expiring_soon'])
    for lease in active_leases:
      due_date_reminder = today + relativedelta(days=5)
      if due_date_reminder.day == 1:
        summary = lease.get_payment_summary()
        for month_summary in summary:
          if month_summary['year'] == due_date_reminder.year and month_summary['month'] == due_date_reminder.month:
            if month_summary['status'] not in ['paid', 'partial']:
              msg = _("تذكير: دفعة ايجار عقد ٪(contracts)s عن شهر ٪(month)s / ٪(year)s تستحق قريبا.")%{'contracts': lease.contract_number, 'month': month_summary['month'], 'year': month_summary['year']}
              if lease.tenant.user:
                Notification.objects.get_or_create(user=lease.tenant.user, message=msg, related_object=lease)
              for user in staff_users:
                Notification.objects.get_or_create(user=user, message=msg, related_object=lease)
              self.stdout.write(f" - Reminder sent for lease {lease.contract_number}")
      summary = lease.get_payment_summary()
      first_day_of_current_month = today.replace(day=1)
      for month_summary in summary:
        month_date = datetime(month_summary['year'], month_summary['month'], 1).date()
        if month_date < first_day_of_current_month and month_summary['balance'] > 0:
          msg = _("تنبيه: يوجد مبلغ متاخر بقيمة %(balance)s على عقد %(contract)s عن شهر %(month)s / %(year)s.") % {'balance': month_summary['balance'], 'contract': lease.contract_number, 'month': month_summary['month'], 'year': month_summary['year']}
          if lease.tenant.user:
            Notification.objects.get_or_create(user=lease.tenant.user, message=msg, related_object=lease)
          for user in staff_users:
            Notification.objects.get_or_create(user=user, message=msg, related_object=lease)
          self.stdout.write(f" - Overdue notice sent for lease {lease.contract_number}")
    self.stdout.write(self.style.SUCCESS(_('Process finished.')))
      