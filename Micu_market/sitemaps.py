from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from listings.models import Listing


class StaticViewSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self):
        return ["listings:home", "listings:list", "pages:about", "pages:terms", "pages:privacy"]

    def location(self, item):
        return reverse(item)


class ListingSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.7
    protocol = "https"
    limit = 2000

    def items(self):
        return Listing.objects.filter(status="active").order_by("-updated_at")

    def lastmod(self, obj):
        return obj.updated_at


SITEMAPS = {
    "static": StaticViewSitemap,
    "listings": ListingSitemap,
}
