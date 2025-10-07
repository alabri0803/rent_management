# إعداد تسجيل الدخول عبر GitHub

## الخطوات المطلوبة

### 1. إنشاء تطبيق GitHub OAuth

1. اذهب إلى [GitHub Developer Settings](https://github.com/settings/developers)
2. انقر على **"New OAuth App"**
3. املأ المعلومات التالية:
   - **Application name**: `Rent Management System`
   - **Homepage URL**: `https://adminalabrialabri.pythonanywhere.com`
   - **Authorization callback URL**: `https://adminalabrialabri.pythonanywhere.com/accounts/github/login/callback/`
4. انقر على **"Register application"**
5. انسخ **Client ID** و **Client Secret**

### 2. إعداد التطبيق في Django

#### الطريقة الأولى: استخدام أمر الإعداد التلقائي

```bash
python manage.py setup_github_oauth
```

سيطلب منك الأمر إدخال Client ID و Client Secret.

#### الطريقة الثانية: الإعداد اليدوي عبر Django Admin

1. سجل الدخول إلى لوحة الإدارة: `/admin/`
2. اذهب إلى **Sites** → **Sites**
3. تأكد من أن الموقع الحالي هو `adminalabrialabri.pythonanywhere.com`
4. اذهب إلى **Social applications** → **Add social application**
5. املأ المعلومات:
   - **Provider**: `GitHub`
   - **Name**: `GitHub`
   - **Client id**: [الصق Client ID من GitHub]
   - **Secret key**: [الصق Client Secret من GitHub]
   - **Sites**: اختر `adminalabrialabri.pythonanywhere.com`
6. احفظ التغييرات

### 3. التحقق من الإعدادات

تأكد من أن الإعدادات التالية موجودة في `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.github',
    # ...
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SITE_ID = 1
```

### 4. اختبار تسجيل الدخول

1. اذهب إلى صفحة تسجيل الدخول
2. انقر على زر **"تسجيل الدخول عبر GitHub"**
3. سيتم توجيهك إلى GitHub للموافقة
4. بعد الموافقة، سيتم إعادة توجيهك إلى التطبيق

## ملاحظات مهمة

- تأكد من أن `SITE_ID` في `settings.py` يطابق ID الموقع في قاعدة البيانات
- URL الخاص بـ callback يجب أن يكون دقيقاً تماماً
- في بيئة التطوير المحلية، استخدم `http://127.0.0.1:8000` بدلاً من `https://...`
- لا تشارك Client Secret مع أي شخص

## استكشاف الأخطاء

### خطأ: "Social app not found"
- تأكد من إضافة التطبيق في Django Admin
- تأكد من ربط التطبيق بالموقع الصحيح

### خطأ: "Redirect URI mismatch"
- تأكد من أن Authorization callback URL في GitHub يطابق URL في التطبيق تماماً
- تأكد من عدم وجود شرطة مائلة إضافية في النهاية

### خطأ: "Invalid client"
- تأكد من صحة Client ID و Client Secret
- تأكد من عدم وجود مسافات إضافية عند النسخ
