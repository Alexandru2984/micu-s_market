from django.contrib import admin

from .models import PaymentWebhookEvent, PromotionOrder, PromotionPlan


@admin.register(PromotionPlan)
class PromotionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "days", "price", "currency", "is_active")
    list_filter = ("is_active", "currency")
    search_fields = ("name",)


@admin.register(PromotionOrder)
class PromotionOrderAdmin(admin.ModelAdmin):
    list_display = ("listing", "user", "plan", "amount", "currency", "status", "created_at")
    list_filter = ("status", "currency", "created_at")
    search_fields = ("listing__title", "user__username", "user__email", "external_reference")
    readonly_fields = ("amount", "currency", "created_at", "paid_at", "applied_at")
    actions = ("mark_paid_and_apply",)

    @admin.action(description="Marchează ca plătită și aplică promovarea")
    def mark_paid_and_apply(self, request, queryset):
        for order in queryset:
            order.mark_paid()
            order.apply_promotion()


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "order", "status", "processed_at", "created_at")
    list_filter = ("provider", "status", "created_at")
    search_fields = ("event_id", "order__listing__title", "order__user__username")
    readonly_fields = ("provider", "event_id", "order", "payload", "status", "processed_at", "created_at")
