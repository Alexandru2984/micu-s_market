from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("anunt/<slug:slug>/promoveaza/", views.promote_listing_view, name="promote_listing"),
    path("comenzi-promovare/<int:pk>/", views.promotion_order_view, name="promotion_order"),
    path("webhooks/promovari/", views.promotion_webhook_view, name="promotion_webhook"),
]
