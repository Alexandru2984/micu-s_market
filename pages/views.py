from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.views.decorators.cache import cache_control
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


@require_GET
@cache_control(public=True, max_age=3600)
def manifest_view(request):
    return JsonResponse(
        {
            "name": "Micu's Market",
            "short_name": "Micu Market",
            "description": "Marketplace pentru anunțuri locale în România.",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#ffffff",
            "theme_color": "#2563eb",
            "lang": "ro-RO",
            "categories": ["shopping", "business"],
            "icons": [
                {
                    "src": static("images/favicon.svg"),
                    "sizes": "any",
                    "type": "image/svg+xml",
                    "purpose": "any maskable",
                }
            ],
        },
        content_type="application/manifest+json",
    )


@require_GET
@cache_control(public=True, max_age=3600)
def service_worker_view(request):
    return render(request, "pages/service-worker.js", content_type="application/javascript")


@require_GET
@cache_control(public=True, max_age=3600)
def offline_view(request):
    return render(request, "pages/offline.html")


def bad_request_view(request, exception):
    return render(request, "pages/errors/400.html", status=400)


def permission_denied_view(request, exception):
    return render(request, "pages/errors/403.html", status=403)


def page_not_found_view(request, exception):
    return render(request, "pages/errors/404.html", status=404)


def server_error_view(request):
    return render(request, "pages/errors/500.html", status=500)
