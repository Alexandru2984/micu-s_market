from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from listings.models import Listing
from categories.models import Category
# Create your views here.


@require_GET
@never_cache
def healthcheck_view(request):
    database_ok = True
    try:
        connections['default'].cursor().execute('SELECT 1')
    except OperationalError:
        database_ok = False

    return JsonResponse(
        {
            'status': 'ok' if database_ok else 'unhealthy',
            'database': 'ok' if database_ok else 'unavailable',
        },
        status=200 if database_ok else 503,
    )


def home_view(request):
    latest = Listing.objects.filter(status='active').order_by('-created_at')[:8]
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
