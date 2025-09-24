from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from dateutil.relativedelta import relativedelta
from dashboard.models import Lease, Notification, Payment
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Sends notifications for expiring leases, upcoming payments, and overdue payments.'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        self.stdout.write(self.style.SUCCESS(f"--- Running Reminders Job on {today} ---"))

        # جلب المستخدمين الموظفين مرة واحدة
        staff_users = User.objects.filter(is_staff=True)
        if not staff_users.exists():
            self.stdout.write(self.style.WARNING("No staff users found to send notifications to."))

        # جلب العقود النشطة أو التي ستنتهي قريباً
        active_leases = Lease.objects.filter(status__in=['active', 'expiring_soon'])

        for lease in active_leases:
            # 1. إشعارات انتهاء العقد (للموظفين)
            self.check_expiring_leases(lease, staff_users)

            # 2. إشعارات تذكير بالدفعات القادمة (للمستأجرين)
            self.check_upcoming_payments(lease, today)

            # 3. إشعارات الدفعات المتأخرة (للمستأجرين والموظفين)
            self.check_overdue_payments(lease, today, staff_users)

        self.stdout.write(self.style.SUCCESS("--- Reminders Job Finished ---"))

    def create_notification_if_not_exists(self, user, message, related_object):
        """ دالة مساعدة لإنشاء إشعار مع التحقق من عدم وجوده مسبقاً """
        # يبحث عن إشعار بنفس الرسالة والمستخدم خلال آخر 30 يوم
        thirty_days_ago = timezone.now() - relativedelta(days=30)
        if not Notification.objects.filter(
            user=user,
            message=message,
            timestamp__gte=thirty_days_ago
        ).exists():
            Notification.objects.create(user=user, message=message, related_object=related_object)
            self.stdout.write(f"  > Notification created for {user.username}: {message}")


    def check_expiring_leases(self, lease, staff_users):
        """ يرسل إشعاراً للموظفين بخصوص العقود التي ستنتهي قريباً """
        if lease.status == 'expiring_soon':
            message = _("تنبيه: عقد المستأجر '{}' رقم {} سينتهي قريباً في تاريخ {}.").format(
                lease.tenant.name, lease.contract_number, lease.end_date.strftime('%Y-%m-%d')
            )
            for user in staff_users:
                self.create_notification_if_not_exists(user, message, lease)


    def check_upcoming_payments(self, lease, today):
        """ يرسل تذكيراً للمستأجر قبل 7 أيام من بداية كل شهر """
        if not lease.tenant.user:
            return # لا يمكن إرسال إشعار بدون حساب مستخدم

        first_day_of_next_month = (today + relativedelta(months=1)).replace(day=1)
        reminder_date = first_day_of_next_month - relativedelta(days=7)

        if today == reminder_date:
            # التحقق إذا كان الشهر القادم ضمن فترة العقد
            if lease.start_date <= first_day_of_next_month <= lease.end_date:
                month_name = _(first_day_of_next_month.strftime('%B'))
                message = _("تذكير: دفعة إيجار شهر {} مستحقة قريباً. قيمة الإيجار: {} ر.ع").format(
                    month_name, lease.monthly_rent
                )
                self.create_notification_if_not_exists(lease.tenant.user, message, lease)


    def check_overdue_payments(self, lease, today, staff_users):
        """ يتحقق من الدفعات المتأخرة ويرسل إشعارات """
        # التحقق من الشهر الحالي فقط
        current_month = today.month
        current_year = today.year

        # تجاهل إذا كان العقد لم يبدأ بعد في هذا الشهر
        if lease.start_date.year > current_year or (lease.start_date.year == current_year and lease.start_date.month > current_month):
            return

        total_paid_for_month = lease.payments.filter(
            payment_for_year=current_year,
            payment_for_month=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        if total_paid_for_month < lease.monthly_rent:
            # إرسال إشعار بعد مرور 5 أيام من بداية الشهر
            if today.day == 5:
                balance = lease.monthly_rent - total_paid_for_month
                month_name = _(today.strftime('%B'))

                # رسالة للمستأجر
                if lease.tenant.user:
                    tenant_message = _("تنبيه تأخير: لم يتم سداد إيجار شهر {} بالكامل. المبلغ المتبقي: {} ر.ع").format(
                        month_name, balance
                    )
                    self.create_notification_if_not_exists(lease.tenant.user, tenant_message, lease)

                # رسالة للموظفين
                staff_message = _("تأخير سداد: المستأجر '{}' لم يسدد إيجار شهر {} بالكامل. المتبقي: {} ر.ع").format(
                    lease.tenant.name, month_name, balance
                )
                for user in staff_users:
                    self.create_notification_if_not_exists(user, staff_message, lease)