from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

# Create your views here.

@login_required
@staff_member_required
def dashboard_home_view(request):
	context = {}
	return render(request, 'dashboard/home.html', context)

@login_required
@staff_member_required
def reports_list_view(request):
	context = {}
	return render(request, 'dashboard/reports.html', context)

@login_required
@staff_member_required
def verify_listings_view(request):
	context = {}
	return render(request, 'dashboard/verify_listings.html', context)
