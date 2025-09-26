from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import Lease, Notification, User
from django.utils.translation import gettext as _
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Checks for due and overdue payments and sends notifications.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting payment check process...'))
        today = timezone.now().date()
        staff_users = User.objects.filter(is_staff=True)

        active_leases = Lease.objects.filter(status__in=['active', 'expiring_soon'])

        for lease in active_leases:
            # --- 1. التحقق من الدفعات المتأخرة (للأشهر السابقة) ---
            summary = lease.get_payment_summary()
            for month_summary in summary:
                # تحقق فقط من الأشهر التي انتهت ولم يتم دفعها بالكامل
                is_past_due = (month_summary['year'] < today.year) or \
                              (month_summary['year'] == today.year and month_summary['month'] < today.month)

                if is_past_due and month_summary['status'] in ['due', 'partial']:
                    # إرسال إشعار للموظفين
                    message_staff = _("تأخير في السداد: دفعة شهر {}/{} للعقد {} لم تسدد بالكامل.").format(
                        month_summary['month'], month_summary['year'], lease.contract_number)
                    for user in staff_users:
                        Notification.objects.get_or_create(
                            user=user, message=message_staff, 
                            defaults={'related_object': lease}
                        )
                    # إرسال إشعار للمستأجر
                    if lease.tenant.user:
                        message_tenant = _("تذكير بسداد: دفعة إيجار شهر {}/{} لم تسدد بالكامل.").format(
                            month_summary['month'], month_summary['year'])
                        Notification.objects.get_or_create(
                            user=lease.tenant.user, message=message_tenant, 
                            defaults={'related_object': lease}
                        )

            # --- 2. التحقق من الدفعات المستحقة (للشهر الحالي) ---
            # إرسال تذكير في أول 5 أيام من الشهر
            if 1 <= today.day <= 5:
                 current_month_summary = next((m for m in summary if m['year'] == today.year and m['month'] == today.month), None)
                 if current_month_summary and current_month_summary['status'] in ['due', 'partial']:
                    message_tenant = _("تذكير ودي: دفعة إيجار هذا الشهر مستحقة الآن. يرجى المبادرة بالسداد.").format(
                        current_month_summary['month'], current_month_summary['year'])
                    if lease.tenant.user:
                        Notification.objects.get_or_create(
                            user=lease.tenant.user, message=message_tenant, 
                            defaults={'related_object': lease}
                        )

        self.stdout.write(self.style.SUCCESS('Payment check process finished.'))