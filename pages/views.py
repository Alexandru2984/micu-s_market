from django.shortcuts import render
from listings.models import Listing
from categories.models import Category
# Create your views here.

def home_view(request):
    latest = Listing.objects.filter(is_active=True)[:8]
    # Get main categories (no parent) for home page
    categories = Category.objects.filter(is_active=True, parent=None)[:12]  # Get 12 categories
    context = {
		"listings": latest,
		"categories": categories,
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
