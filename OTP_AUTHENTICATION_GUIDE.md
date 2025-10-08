# دليل نظام تسجيل الدخول المحسن - OTP Authentication Guide

## نظرة عامة / Overview

تم تحسين نظام تسجيل الدخول ليدعم طريقتين للتحقق:
1. **تسجيل الدخول بكلمة المرور** - الطريقة التقليدية
2. **تسجيل الدخول برمز التحقق (OTP)** - عبر الرسائل النصية

The login system has been enhanced to support two authentication methods:
1. **Password Login** - Traditional method
2. **OTP Login** - Via SMS verification codes

## الميزات الجديدة / New Features

### 1. نماذج البيانات الجديدة / New Models

#### UserProfile Model
- يربط المستخدمين بأرقام الهواتف
- Links users to phone numbers
- Fields: `user`, `phone_number`

#### OTP Model  
- يخزن رموز التحقق المؤقتة
- Stores temporary verification codes
- Fields: `user`, `code`, `phone_number`, `created_at`, `expires_at`, `is_used`, `purpose`

### 2. خدمات OTP / OTP Services

#### OTPService Class
- إنشاء رموز التحقق
- Generate verification codes
- التحقق من صحة الرموز
- Validate verification codes
- إرسال الرسائل النصية
- Send SMS messages
- إدارة معدل الطلبات
- Rate limiting management

#### SMSService Class
- دعم متعدد لمقدمي الخدمة
- Multi-provider support
- Twilio integration
- AWS SNS integration
- Console mode للتطوير
- Console mode for development

### 3. واجهات المستخدم المحسنة / Enhanced UI

#### صفحة تسجيل الدخول
- تبويبات للاختيار بين كلمة المرور و OTP
- Tabs to choose between password and OTP
- واجهة تفاعلية لطلب رمز التحقق
- Interactive interface for requesting verification codes
- إدخال تلقائي للرمز
- Auto-submission when 6 digits entered

#### صفحة الملف الشخصي
- إدارة أرقام الهواتف
- Phone number management
- عرض طرق تسجيل الدخول المتاحة
- Display available login methods

## الإعداد والتكوين / Setup and Configuration

### 1. تشغيل الترحيلات / Run Migrations

```bash
python manage.py migrate
```

### 2. تكوين خدمة الرسائل النصية / SMS Service Configuration

#### للاستخدام في التطوير / For Development
```python
# settings.py
SMS_PROVIDER = 'console'  # Default - displays SMS in console
```

#### لتويليو / For Twilio
```python
# settings.py
SMS_PROVIDER = 'twilio'
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'
```

#### لـ AWS SNS / For AWS SNS
```python
# settings.py
SMS_PROVIDER = 'aws_sns'
AWS_ACCESS_KEY_ID = 'your_access_key'
AWS_SECRET_ACCESS_KEY = 'your_secret_key'
AWS_SNS_REGION = 'us-east-1'
```

### 3. تثبيت المكتبات الاختيارية / Install Optional Libraries

```bash
# لتويليو / For Twilio
pip install twilio

# لـ AWS SNS / For AWS SNS  
pip install boto3
```

## كيفية الاستخدام / How to Use

### 1. إعداد رقم الهاتف للمستخدم / Setting Up Phone Number for User

#### عبر الواجهة الإدارية / Via Admin Interface
1. انتقل إلى `/admin/`
2. Go to `/admin/`
3. ابحث عن "User Profiles"
4. Look for "User Profiles"
5. أضف ملف مستخدم جديد مع رقم الهاتف
6. Add new user profile with phone number

#### عبر واجهة المستخدم / Via User Interface
1. سجل الدخول بحسابك
2. Login to your account
3. انتقل إلى `/dashboard/profile/`
4. Go to `/dashboard/profile/`
5. اضغط على "إضافة رقم هاتف"
6. Click "Add Phone Number"
7. أدخل رقم هاتفك
8. Enter your phone number
9. تحقق من الرقم عبر OTP
10. Verify the number via OTP

### 2. تسجيل الدخول عبر OTP / OTP Login

1. انتقل إلى صفحة تسجيل الدخول
2. Go to login page
3. اختر تبويب "رمز التحقق"
4. Choose "Verification Code" tab
5. أدخل رقم هاتفك
6. Enter your phone number
7. اضغط "إرسال رمز التحقق"
8. Click "Send Verification Code"
9. أدخل الرمز المرسل إليك
10. Enter the code sent to you
11. سيتم تسجيل دخولك تلقائياً
12. You will be logged in automatically

## API Endpoints / نقاط النهاية

### 1. إرسال OTP / Send OTP
```
POST /api/auth/send-otp/
Content-Type: application/x-www-form-urlencoded

phone_number=+966501234567
```

### 2. التحقق من OTP / Verify OTP
```
POST /api/auth/verify-otp/
Content-Type: application/x-www-form-urlencoded

phone_number=+966501234567&otp_code=123456
```

### 3. إرسال OTP للتحقق من الهاتف / Send Phone Verification OTP
```
POST /api/auth/send-phone-otp/
Content-Type: application/x-www-form-urlencoded
```

## الأمان / Security Features

### 1. انتهاء صلاحية الرموز / Code Expiration
- رموز OTP صالحة لمدة 5 دقائق فقط
- OTP codes valid for 5 minutes only

### 2. حد المحاولات / Rate Limiting
- حد أقصى 3 محاولات إرسال OTP في الساعة
- Maximum 3 OTP sending attempts per hour

### 3. استخدام الرموز / Code Usage
- كل رمز يستخدم مرة واحدة فقط
- Each code can be used only once

### 4. تنظيف تلقائي / Automatic Cleanup
- حذف الرموز المنتهية الصلاحية تلقائياً
- Automatic deletion of expired codes

## استكشاف الأخطاء / Troubleshooting

### 1. لا يتم إرسال الرسائل النصية / SMS Not Being Sent

#### تحقق من الإعدادات / Check Settings
```python
# تأكد من صحة الإعدادات
# Ensure correct settings
SMS_PROVIDER = 'twilio'  # أو 'aws_sns' أو 'console'
```

#### تحقق من السجلات / Check Logs
```bash
# ابحث عن أخطاء SMS في سجلات Django
# Look for SMS errors in Django logs
tail -f logs/django.log | grep SMS
```

### 2. لا يمكن العثور على المستخدم / User Not Found

#### تأكد من وجود الملف الشخصي / Ensure Profile Exists
```python
# تحقق من وجود UserProfile للمستخدم
# Check if UserProfile exists for user
from dashboard.models import UserProfile
profile = UserProfile.objects.filter(user=user).first()
if not profile:
    # إنشاء ملف شخصي جديد
    # Create new profile
    profile = UserProfile.objects.create(user=user, phone_number=phone_number)
```

### 3. مشاكل في قاعدة البيانات / Database Issues

#### تشغيل الترحيلات / Run Migrations
```bash
python manage.py makemigrations dashboard
python manage.py migrate
```

#### إنشاء ملفات الترجمة / Create Translation Files
```bash
python manage.py makemessages -l ar
python manage.py compilemessages
```

## التخصيص / Customization

### 1. تخصيص مدة انتهاء الصلاحية / Customize Expiration Time

```python
# dashboard/otp_service.py
class OTPService:
    OTP_EXPIRY_MINUTES = 10  # تغيير من 5 إلى 10 دقائق
```

### 2. تخصيص حد المحاولات / Customize Rate Limit

```python
# dashboard/otp_service.py
class OTPService:
    MAX_OTP_ATTEMPTS = 5  # تغيير من 3 إلى 5 محاولات
```

### 3. تخصيص طول رمز OTP / Customize OTP Length

```python
# dashboard/models.py
class OTP(models.Model):
    @classmethod
    def generate_code(cls, length=8):  # تغيير من 6 إلى 8 أرقام
        return ''.join(secrets.choice(string.digits) for _ in range(length))
```

## الاختبار / Testing

### 1. اختبار في وضع التطوير / Testing in Development Mode

```python
# settings.py
SMS_PROVIDER = 'console'  # سيعرض الرسائل في وحدة التحكم
```

### 2. اختبار API / Testing API

```bash
# إرسال OTP
curl -X POST http://localhost:8000/api/auth/send-otp/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "phone_number=+966501234567"

# التحقق من OTP
curl -X POST http://localhost:8000/api/auth/verify-otp/ \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "phone_number=+966501234567&otp_code=123456"
```

## الصيانة / Maintenance

### 1. تنظيف الرموز المنتهية الصلاحية / Cleanup Expired Codes

```python
# يمكن تشغيل هذا كـ cron job
from dashboard.models import OTP
from django.utils import timezone

# حذف الرموز المنتهية الصلاحية
expired_otps = OTP.objects.filter(expires_at__lt=timezone.now())
expired_otps.delete()
```

### 2. مراقبة الإحصائيات / Monitor Statistics

```python
# إحصائيات OTP
from dashboard.models import OTP
from django.utils import timezone
from datetime import timedelta

# عدد OTP المرسلة اليوم
today_otps = OTP.objects.filter(
    created_at__gte=timezone.now().date()
).count()

# معدل النجاح
successful_otps = OTP.objects.filter(is_used=True).count()
total_otps = OTP.objects.count()
success_rate = (successful_otps / total_otps) * 100 if total_otps > 0 else 0
```

## الدعم / Support

للحصول على المساعدة أو الإبلاغ عن مشاكل:
For help or to report issues:

1. تحقق من سجلات Django
2. Check Django logs
3. تأكد من صحة الإعدادات
4. Verify configuration settings
5. اختبر في وضع التطوير أولاً
6. Test in development mode first

---

**ملاحظة**: هذا النظام متوافق مع النسخ الحالية من Django ويستخدم أفضل الممارسات الأمنية.
**Note**: This system is compatible with current Django versions and uses security best practices.
