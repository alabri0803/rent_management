from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = 'Setup GitHub OAuth application for django-allauth'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== إعداد GitHub OAuth ===\n'))
        
        # الحصول على الموقع الحالي
        site = Site.objects.get_current()
        
        self.stdout.write(f'الموقع الحالي: {site.domain}\n')
        
        # طلب معلومات GitHub OAuth من المستخدم
        self.stdout.write(self.style.WARNING('\nيرجى اتباع الخطوات التالية لإعداد GitHub OAuth:\n'))
        self.stdout.write('1. اذهب إلى: https://github.com/settings/developers')
        self.stdout.write('2. انقر على "New OAuth App"')
        self.stdout.write('3. املأ المعلومات التالية:')
        self.stdout.write(f'   - Application name: Rent Management System')
        self.stdout.write(f'   - Homepage URL: http://{site.domain}')
        self.stdout.write(f'   - Authorization callback URL: http://{site.domain}/accounts/github/login/callback/')
        self.stdout.write('4. انقر على "Register application"')
        self.stdout.write('5. انسخ Client ID و Client Secret\n')
        
        client_id = input('أدخل GitHub Client ID: ').strip()
        client_secret = input('أدخل GitHub Client Secret: ').strip()
        
        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR('خطأ: يجب إدخال Client ID و Client Secret'))
            return
        
        # إنشاء أو تحديث تطبيق GitHub
        github_app, created = SocialApp.objects.get_or_create(
            provider='github',
            defaults={
                'name': 'GitHub',
                'client_id': client_id,
                'secret': client_secret,
            }
        )
        
        if not created:
            github_app.client_id = client_id
            github_app.secret = client_secret
            github_app.save()
            self.stdout.write(self.style.SUCCESS('\n✓ تم تحديث تطبيق GitHub بنجاح'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ تم إنشاء تطبيق GitHub بنجاح'))
        
        # ربط التطبيق بالموقع
        github_app.sites.add(site)
        
        self.stdout.write(self.style.SUCCESS(f'✓ تم ربط التطبيق بالموقع: {site.domain}'))
        self.stdout.write(self.style.SUCCESS('\n=== اكتمل الإعداد بنجاح! ===\n'))
        self.stdout.write('يمكنك الآن استخدام تسجيل الدخول عبر GitHub')
