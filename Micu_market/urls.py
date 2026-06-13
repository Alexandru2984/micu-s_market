from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from pages.views import healthcheck_view, manifest_view, offline_view, service_worker_view

urlpatterns = [
    path("healthz", healthcheck_view, name="healthcheck"),
    path("manifest.webmanifest", manifest_view, name="manifest"),
    path("sw.js", service_worker_view, name="service_worker"),
    path("offline/", offline_view, name="offline"),
    path(settings.ADMIN_URL, admin.site.urls),

    # Django Allauth URLs
    path("accounts/", include("allauth.urls")),
    
    # Homepage
    path("", include(("listings.urls", "listings"), namespace="listings")),
    
    # Aplicații
    path("pages/", include(("pages.urls", "pages"), namespace="pages")),
    path("accounts/custom/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("categories/", include(("categories.urls", "categories"), namespace="categories")),
    path("search/", include(("search.urls", "search"), namespace="search")),
    path("chat/", include(("chat.urls", "chat"), namespace="chat")),
    path("reviews/", include(("reviews.urls", "reviews"), namespace="reviews")),
    path("favorites/", include(("favorites.urls", "favorites"), namespace="favorites")),
    path("notifications/", include(("notifications.urls", "notifications"), namespace="notifications")),
    path("dashboard/", include(("dashboard.urls", "dashboard"), namespace="dashboard")),
    path("api/", include(("api.urls", "api"), namespace="api")),
    path("billing/", include(("billing.urls", "billing"), namespace="billing")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
