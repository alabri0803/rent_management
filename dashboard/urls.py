from django.urls import path
from . import views

urlpatterns = [
  path('', views.lease_management, name='lease_management'),
]