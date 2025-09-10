from django.shortcuts import render
from listings.models import Listing
# Create your views here.

def home_view(request):
    latest = Listing.objects.filter(is_active=True)[:8]
    context = {
		"listings": latest,
	}
    return render(request, "pages/home.html", context)

def about_view(request):
	context = {}
	return render(request, 'pages/about.html', context)

def contact_view(request):
	context = {}
	return render(request, 'pages/contact.html', context)

def terms_view(request):
	context = {}
	return render(request, 'pages/terms.html', context)

def privacy_view(request):
	context = {}
	return render(request, 'pages/privacy.html', context)
