from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
from django_ratelimit.decorators import ratelimit

from .models import Notification

# Create your views here.

@login_required
def notifications_list_view(request):
    notifications_qs = Notification.objects.filter(
        recipient=request.user
    )

    context = {
        'notifications': notifications_qs.order_by('-created_at')[:50],
        'unread_count': notifications_qs.filter(is_read=False).count(),
    }
    return render(request, 'notifications/list.html', context)

@login_required
@require_POST
@ratelimit(key='user', rate=settings.AJAX_WRITE_RATE, method='POST', block=True)
def mark_read_view(request, pk=None):
    """Mark one notification (or all) as read"""
    if pk:
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        notification.mark_as_read()
    else:
        # Mark all as read
        Notification.objects.filter(
            recipient=request.user,
            is_read=False
        ).update(is_read=True)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('notifications:list')
