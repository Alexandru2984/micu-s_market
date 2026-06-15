from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from pages.views import healthcheck_view, manifest_view, offline_view, robots_txt, service_worker_view
from Micu_market.sitemaps import SITEMAPS

urlpatterns = [
    path("healthz", healthcheck_view, name="healthcheck"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("manifest.webmanifest", manifest_view, name="manifest"),
    path("sw.js", service_worker_view, name="service_worker"),
    path("offline/", offline_view, name="offline"),
    path(settings.ADMIN_URL, admin.site.urls),

    # Language switcher (set_language redirect view)
    path("i18n/", include("django.conf.urls.i18n")),

    # Django Allauth URLs
    path("accounts/", include("allauth.urls")),
    
    # Homepage
    path("", include(("listings.urls", "listings"), namespace="listings")),
    
    # Apps
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

handler400 = "pages.views.bad_request_view"
handler403 = "pages.views.permission_denied_view"
handler404 = "pages.views.page_not_found_view"
handler500 = "pages.views.server_error_view"
