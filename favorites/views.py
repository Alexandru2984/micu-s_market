from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from listings.models import Listing

from .models import Favorite


@login_required
def favorites_list_view(request):
    """The user's list of favorite listings"""
    favorites = Favorite.objects.filter(user=request.user).select_related('listing', 'listing__category', 'listing__owner').prefetch_related('listing__images')

    # Pagination
    paginator = Paginator(favorites, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_favorites': favorites.count()
    }
    return render(request, 'favorites/list.html', context)

@login_required
@require_POST
@ratelimit(key='user', rate=settings.AJAX_WRITE_RATE, method='POST', block=True)
def toggle_favorite_view(request):
    """Toggle favorite for a listing (AJAX)"""
    listing_id = request.POST.get('listing_id')
    
    if not listing_id:
        return JsonResponse({'error': 'Listing ID is required'}, status=400)
    
    try:
        listing = get_object_or_404(Listing, id=listing_id, status='active')
        
        # Make sure the user is not trying to favorite their own listing
        if listing.owner == request.user:
            return JsonResponse({'error': 'Nu poți adăuga propriile anunțuri la favorite'}, status=400)
        
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            listing=listing
        )
        
        if not created:
            # If the favorite already exists, remove it
            favorite.delete()
            is_favorited = False
            message = 'Anunțul a fost eliminat din favorite'
        else:
            # If it did not exist, it was just created
            is_favorited = True
            message = 'Anunțul a fost adăugat la favorite'
        
        response_data = {
            'success': True,
            'is_favorited': is_favorited,
            'message': message,
            'favorites_count': Favorite.objects.filter(user=request.user).count()
        }
        
        return JsonResponse(response_data)
        
    except Listing.DoesNotExist:
        return JsonResponse({'error': 'Anunțul nu a fost găsit'}, status=404)
    except Exception:
        return JsonResponse({'error': 'A apărut o eroare'}, status=500)

@login_required
@require_POST
@ratelimit(key='user', rate=settings.AJAX_WRITE_RATE, method='POST', block=True)
def remove_favorite_view(request, favorite_id):
    """Remove an item from the favorites list"""
    favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user)
    listing_title = favorite.listing.title
    favorite.delete()
    
    messages.success(request, f'Anunțul "{listing_title}" a fost eliminat din favorite.')
    return redirect('favorites:list')
