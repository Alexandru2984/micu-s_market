from django.shortcuts import render

# Create your views here.

def dashboard_home_view(request):
	context = {}
	return render(request, 'dashboard/home.html', context)

def reports_list_view(request):
	context = {}
	return render(request, 'dashboard/reports.html', context)

def verify_listings_view(request):
	context = {}
	return render(request, 'dashboard/verify_listings.html', context)
