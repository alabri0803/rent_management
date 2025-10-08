r"""
URL configuration for rent_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib.auth import views as auth_views
from dashboard.views import login_redirect
from dashboard.auth_views import EnhancedLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')), # Language switcher URL
    # Root homepage → portal (non-localized fallback)
    path('', include('portal.urls')),
]

# Language-prefixed URLs
urlpatterns += i18n_patterns(
    path('login-redirect/', login_redirect, name='login_redirect'),
    path('accounts/login/', EnhancedLoginView.as_view(), name='login'),  # Override default login
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('portal/', include('portal.urls')), # Portal is the homepage
    prefix_default_language=True # Don't prefix the default language (ar)
)

# Add OTP authentication endpoints (not language-prefixed for API compatibility)
from dashboard.auth_views import send_login_otp, verify_login_otp
from dashboard.otp_views import send_phone_verification_otp

urlpatterns += [
    path('api/auth/send-otp/', send_login_otp, name='api_send_login_otp'),
    path('api/auth/verify-otp/', verify_login_otp, name='api_verify_login_otp'),
    path('api/auth/send-phone-otp/', send_phone_verification_otp, name='api_send_phone_otp'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)