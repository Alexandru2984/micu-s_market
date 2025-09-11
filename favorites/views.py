from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Favorite
from listings.models import Listing

@login_required
def favorites_list_view(request):
    """Lista anunțurilor favorite ale utilizatorului"""
    favorites = Favorite.objects.filter(user=request.user).select_related('listing', 'listing__category', 'listing__owner').prefetch_related('listing__images')
    
    # Paginare
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
def toggle_favorite_view(request):
    """Toggle favorite pentru un anunț (AJAX)"""
    listing_id = request.POST.get('listing_id')
    
    if not listing_id:
        return JsonResponse({'error': 'Listing ID is required'}, status=400)
    
    try:
        listing = get_object_or_404(Listing, id=listing_id, status='active')
        
        # Verifică dacă utilizatorul nu încearcă să adauge propriul anunț
        if listing.owner == request.user:
            return JsonResponse({'error': 'Nu poți adăuga propriile anunțuri la favorite'}, status=400)
        
        favorite, created = Favorite.objects.get_or_create(
            user=request.user,
            listing=listing
        )
        
        if not created:
            # Dacă favoritul există deja, îl șterge
            favorite.delete()
            is_favorited = False
            message = 'Anunțul a fost eliminat din favorite'
        else:
            # Dacă nu există, l-a creat
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
    except Exception as e:
        return JsonResponse({'error': 'A apărut o eroare'}, status=500)

@login_required
def remove_favorite_view(request, favorite_id):
    """Șterge un favorit din lista de favorite"""
    favorite = get_object_or_404(Favorite, id=favorite_id, user=request.user)
    listing_title = favorite.listing.title
    favorite.delete()
    
    messages.success(request, f'Anunțul "{listing_title}" a fost eliminat din favorite.')
    return redirect('favorites:list')
