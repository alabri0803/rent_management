from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from django.utils.translation import gettext_lazy as _
from .models import Tenant, MaintenanceRequest, Lease, Notification

@receiver(post_save, sender=Tenant)
def create_tenant_user_account(sender, instance, created, **kwargs):
    if created and not instance.user:
        if instance.email:
            username = instance.email.split('@')[0]
        else:
            username = f"user_{instance.phone}"
        if User.objects.filter(username=username).exists():
            username = f"{username}_{instance.id}"
            
        user = User.objects.create_user(username=username, email=instance.email, password=instance.phone)
        user.first_name = instance.name
        try:
            tenant_group = Group.objects.get(name='tenant')
            user.groups.add(tenant_group)
        except Group.DoesNotExist:
            pass
        user.save()
        instance.user = user
        instance.save()

@receiver(post_save, sender=MaintenanceRequest)
def maintenance_request_notification(sender, instance, created, **kwargs):
    if created:
        message = _("'تم تقديم طلب صيانة جديد بعنوان {} من قبل المستأجر {}'").format(instance.title, instance.lease.tenant.name)
        staff_users = User.objects.filter(is_staff=True)
        for user in staff_users:
            Notification.objects.create(user=user, message=message, related_object=instance)
    else:
        try:
            old_instance = MaintenanceRequest.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                message = _("'تم تحديث حالة طلب الصيانة {} إلى {}'").format(instance.title, instance.get_status_display())
                if instance.lease.tenant.user:
                    Notification.objects.create(user=instance.lease.tenant.user, message=message, related_object=instance)
        except MaintenanceRequest.DoesNotExist:
            pass

@receiver(post_save, sender=Lease)
def lease_status_notification(sender, instance, **kwargs):
    if instance.status == 'expiring_soon' and instance.tenant.user:
        message = _("'عقد الإيجار الخاص بك رقم {} سينتهي قريب في تاريخ {}'").format(instance.contract_number, instance.end_date.strftime('%Y-%m-%d'))
        if not Notification.objects.filter(user=instance.tenant.user, message=message).exists():
            Notification.objects.create(user=instance.tenant.user, message=message, related_object=instance)