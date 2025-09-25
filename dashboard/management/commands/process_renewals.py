from django.core.management.base import BaseCommand
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from dashboard.models import Lease
from django.utils.translation import gettext as _

class Command(BaseCommand):
    help = 'Checks for expiring leases with auto-renew enabled and creates new leases for them.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting automatic lease renewal process...'))

        # البحث عن العقود التي انتهت أو ستنتهي قريباً ومفعل بها التجديد التلقائي
        today = timezone.now().date()
        leases_to_renew = Lease.objects.filter(
            end_date__lte=today, 
            status__in=['active', 'expiring_soon', 'expired'],
            auto_renew=True
        )

        renewed_count = 0
        for lease in leases_to_renew:
            # التحقق من عدم وجود عقد جديد لنفس الوحدة
            if Lease.objects.filter(unit=lease.unit, start_date__gt=lease.end_date).exists():
                self.stdout.write(self.style.WARNING(f'Skipping renewal for {lease.contract_number}, new lease already exists.'))
                continue

            # تحديد مدة العقد القديم لتجديده بنفس المدة
            duration = relativedelta(lease.end_date, lease.start_date)

            new_start_date = lease.end_date + relativedelta(days=1)
            new_end_date = new_start_date + duration

            # إنشاء العقد الجديد
            new_lease = Lease.objects.create(
                unit=lease.unit,
                tenant=lease.tenant,
                template=lease.template,
                contract_number=f"{lease.contract_number}-R{today.year}",
                monthly_rent=lease.monthly_rent, # يمكن تعديل هذا المنطق لزيادة الإيجار
                start_date=new_start_date,
                end_date=new_end_date,
                auto_renew=True # جعل العقد الجديد يجدد تلقائياً أيضاً
            )

            # تحديث حالة العقد القديم
            lease.status = 'expired'
            lease.auto_renew = False # إيقاف التجديد في العقد القديم
            lease.save()

            renewed_count += 1
            self.stdout.write(f'  - Renewed lease {lease.contract_number}. New lease is {new_lease.contract_number}.')

        self.stdout.write(self.style.SUCCESS(f'Process finished. Renewed {renewed_count} leases.'))