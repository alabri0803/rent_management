from django.shortcuts import render
from .models import Lease

def lease_management(request):
  lease = Lease.objects.all()
  context = {
    'lease': lease
  }
  return render(request, 'dashboard/lease_list.html', context)