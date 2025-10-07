#!/bin/bash

# ====================================
# أوامر إعداد GitHub OAuth
# ====================================

echo "=== بدء إعداد GitHub OAuth ==="

# 1. تجميع الترجمات
echo "1. تجميع الترجمات..."
python3 manage.py compilemessages

# 2. تشغيل أمر الإعداد
echo "2. إعداد GitHub OAuth..."
python3 manage.py setup_github_oauth

# 3. إعادة تشغيل الخادم (اختياري)
echo "3. يمكنك الآن إعادة تشغيل الخادم"
echo ""
echo "=== اكتمل الإعداد ==="
echo ""
echo "الخطوات التالية:"
echo "1. اذهب إلى https://github.com/settings/developers"
echo "2. أنشئ OAuth App جديد"
echo "3. استخدم هذه المعلومات:"
echo "   - Homepage URL: https://adminalabrialabri.pythonanywhere.com"
echo "   - Callback URL: https://adminalabrialabri.pythonanywhere.com/accounts/github/login/callback/"
echo "4. شغل الأمر: python3 manage.py setup_github_oauth"
echo "5. أدخل Client ID و Client Secret"
echo ""
