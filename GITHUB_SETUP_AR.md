# دليل إعداد تسجيل الدخول عبر GitHub

## ✅ ما تم إنجازه

### 1. إضافة زر تسجيل الدخول عبر GitHub
- ✓ تم إضافة زر GitHub إلى صفحة تسجيل الدخول
- ✓ تصميم جميل ومتناسق مع بقية الصفحة
- ✓ أيقونة GitHub الرسمية
- ✓ دعم كامل للغة العربية والإنجليزية

### 2. الإعدادات الخلفية
- ✓ تكوين django-allauth لدعم GitHub
- ✓ إنشاء أمر إعداد تلقائي: `setup_github_oauth`
- ✓ جميع الإعدادات المطلوبة في settings.py موجودة
- ✓ URLs جاهزة للاستخدام

### 3. الترجمات
- ✓ "أو تسجيل الدخول عبر" → "Or sign in with"
- ✓ "تسجيل الدخول عبر GitHub" → "Sign in with GitHub"
- ✓ تم تجميع الترجمات بنجاح

## 📋 خطوات الإعداد النهائية

### الخطوة 1: إنشاء تطبيق GitHub OAuth

1. اذهب إلى: https://github.com/settings/developers
2. انقر على **"New OAuth App"**
3. املأ النموذج:

```
Application name: Rent Management System
Homepage URL: https://adminalabrialabri.pythonanywhere.com
Authorization callback URL: https://adminalabrialabri.pythonanywhere.com/accounts/github/login/callback/
```

4. انقر على **"Register application"**
5. ستحصل على:
   - **Client ID** (مثل: Iv1.a1b2c3d4e5f6g7h8)
   - **Client Secret** (انقر على "Generate a new client secret")

⚠️ **مهم**: احفظ Client Secret في مكان آمن - لن تتمكن من رؤيته مرة أخرى!

### الخطوة 2: إعداد التطبيق في Django

#### الطريقة السهلة (موصى بها):

```bash
python3 manage.py setup_github_oauth
```

سيطلب منك:
1. إدخال Client ID
2. إدخال Client Secret

#### الطريقة اليدوية (عبر Admin Panel):

1. اذهب إلى: https://adminalabrialabri.pythonanywhere.com/admin/
2. سجل الدخول كمدير
3. اذهب إلى **Social applications** → **Add social application**
4. املأ:
   - Provider: **GitHub**
   - Name: **GitHub**
   - Client id: [الصق من GitHub]
   - Secret key: [الصق من GitHub]
   - Sites: اختر **adminalabrialabri.pythonanywhere.com**
5. احفظ

### الخطوة 3: اختبار تسجيل الدخول

1. اذهب إلى: https://adminalabrialabri.pythonanywhere.com/accounts/login/
2. ستجد زر **"تسجيل الدخول عبر GitHub"**
3. انقر عليه
4. سيتم توجيهك إلى GitHub للموافقة
5. بعد الموافقة، سيتم تسجيل دخولك تلقائياً

## 🎯 الملفات المضافة/المعدلة

### ملفات جديدة:
- `dashboard/management/commands/setup_github_oauth.py` - أمر الإعداد التلقائي
- `GITHUB_OAUTH_SETUP.md` - دليل الإعداد بالإنجليزية
- `GITHUB_SETUP_AR.md` - هذا الملف (دليل بالعربية)
- `SETUP_COMMANDS.sh` - سكريبت الإعداد
- `COMMIT_MESSAGE.txt` - رسالة commit مناسبة

### ملفات معدلة:
- `templates/registration/login.html` - إضافة زر GitHub
- `locale/en/LC_MESSAGES/django.po` - الترجمات الإنجليزية
- `locale/ar/LC_MESSAGES/django.po` - الترجمات العربية

## 🔧 استكشاف الأخطاء

### المشكلة: "Social app not found"
**الحل**: تأكد من إضافة التطبيق في Django Admin وربطه بالموقع الصحيح

### المشكلة: "Redirect URI mismatch"
**الحل**: تأكد من أن URL في GitHub يطابق تماماً:
```
https://adminalabrialabri.pythonanywhere.com/accounts/github/login/callback/
```

### المشكلة: "Invalid client"
**الحل**: 
- تحقق من Client ID و Client Secret
- تأكد من عدم وجود مسافات إضافية
- تأكد من نسخ Secret كاملاً

## 📝 رسالة Commit المقترحة

```
feat: Add GitHub OAuth login integration

- Added GitHub login button to login page
- Created setup_github_oauth management command
- Added Arabic & English translations
- Included comprehensive setup documentation

Files:
- templates/registration/login.html (modified)
- dashboard/management/commands/setup_github_oauth.py (new)
- GITHUB_OAUTH_SETUP.md (new)
- locale/*/django.po (modified)
```

## 🎨 المظهر النهائي

صفحة تسجيل الدخول الآن تحتوي على:
1. نموذج تسجيل الدخول التقليدي (اسم المستخدم وكلمة المرور)
2. خط فاصل مع نص "أو تسجيل الدخول عبر"
3. زر GitHub بتصميم احترافي مع الأيقونة

## ✨ مميزات إضافية

- ✅ التوجيه التلقائي حسب نوع المستخدم (مدير/مستأجر)
- ✅ دعم كامل للغتين العربية والإنجليزية
- ✅ تصميم متجاوب (Responsive)
- ✅ أمان عالي باستخدام OAuth 2.0
- ✅ سهولة الإعداد والصيانة

## 📞 الدعم

إذا واجهت أي مشكلة:
1. راجع قسم "استكشاف الأخطاء" أعلاه
2. تحقق من سجلات الأخطاء (logs)
3. تأكد من صحة جميع الإعدادات

---

**ملاحظة**: لا تشارك Client Secret مع أي شخص ولا تضعه في Git!
