from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import Tenant, MaintenanceRequest, Lease, Notification, Building, Expense
from .utils import auto_translate_to_english

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


@receiver(pre_save, sender=Building)
def auto_translate_building(sender, instance, **kwargs):
    if instance.name_ar and not instance.name_en:
        instance.name_en = auto_translate_to_english(instance.name_ar)
    if instance.address_ar and not instance.address_en:
        instance.address_en = auto_translate_to_english(instance.address_ar)


@receiver(pre_save, sender=Tenant)
def auto_translate_tenant(sender, instance, **kwargs):
    if instance.name and not hasattr(instance, 'name_en'):
        instance.name_en = auto_translate_to_english(instance.name)
    elif hasattr(instance, 'name_ar') and instance.name_ar and not instance.name_en:
        instance.name_en = auto_translate_to_english(instance.name_ar)
    
    if hasattr(instance, 'authorized_signatory_ar') and instance.authorized_signatory_ar and not instance.authorized_signatory_en:
        instance.authorized_signatory_en = auto_translate_to_english(instance.authorized_signatory_ar)


@receiver(pre_save, sender=Expense)
def auto_translate_expense(sender, instance, **kwargs):
    if instance.description_ar and not instance.description_en:
        instance.description_en = auto_translate_to_english(instance.description_ar)