from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Listing, ListingImage
from .forms import ListingForm, ListingImageFormSet
from categories.models import Category

def home_view(request):
    """Homepage cu anunțuri recente și categorii"""
    recent_listings = Listing.objects.filter(status='active').select_related('category', 'owner').prefetch_related('images').order_by('-created_at')[:8]
    featured_listings = Listing.objects.filter(status='active', is_featured=True).select_related('category', 'owner').prefetch_related('images').order_by('-created_at')[:4]
    popular_categories = Category.objects.filter(is_active=True).annotate(
        listing_count=Count('listings')
    ).order_by('-listing_count')[:6]
    
    # Debug complet
    print("=== HOME VIEW DEBUG ===")
    print(f"Recent listings count: {recent_listings.count()}")
    for listing in recent_listings:
        print(f"- {listing.title}: {listing.images.count()} images")
        if listing.images.first():
            print(f"  First image: {listing.images.first().image.url}")
    
    print(f"Featured listings count: {featured_listings.count()}")
    print(f"Categories count: {popular_categories.count()}")
    
    context = {
        'recent_listings': recent_listings,
        'featured_listings': featured_listings,
        'popular_categories': popular_categories,
    }
    return render(request, 'listings/home.html', context)

def listing_list_view(request):
    """Lista anunțurilor cu filtrare și sortare"""
    listings = Listing.objects.filter(status='active').select_related('category', 'owner').prefetch_related('images')
    
    # Filtrare după categorie
    category_id = request.GET.get('category')
    if category_id:
        listings = listings.filter(category_id=category_id)
    
    # Filtrare după preț
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        listings = listings.filter(price__gte=min_price)
    if max_price:
        listings = listings.filter(price__lte=max_price)
    
    # Filtrare după oraș
    city = request.GET.get('city')
    if city:
        listings = listings.filter(city__icontains=city)
    
    # Căutare
    search = request.GET.get('search')
    if search:
        listings = listings.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Sortare
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'title', '-title']
    if sort_by in valid_sorts:
        listings = listings.order_by(sort_by)
    else:
        listings = listings.order_by('-created_at')
    
    # Paginare
    paginator = Paginator(listings, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Context pentru template
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': category_id,
        'current_city': city,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search,
        'sort_by': sort_by,
    }
    return render(request, 'listings/list.html', context)

def listing_detail_view(request, slug):
    """Detaliile unui anunț"""
    listing = get_object_or_404(Listing, slug=slug, status='active')
    
    # Crește numărul de vizualizări
    listing.views_count += 1
    listing.save(update_fields=['views_count'])
    
    # Anunțuri similare
    similar_listings = Listing.objects.filter(
        category=listing.category,
        status='active'
    ).exclude(id=listing.id).prefetch_related('images')[:4]
    
    context = {
        'listing': listing,
        'similar_listings': similar_listings,
    }
    return render(request, 'listings/detail.html', context)

@login_required
def listing_create_view(request):
    """Creează anunț nou"""
    if request.method == 'POST':
        form = ListingForm(request.POST)
        
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            
            # Procesează imaginile
            images = request.FILES.getlist('images')
            for image in images:
                if image:
                    try:
                        ListingImage.objects.create(
                            listing=listing,
                            image=image,
                            alt_text=f"Imagine pentru {listing.title}"
                        )
                    except Exception as e:
                        messages.warning(request, f'Nu am putut încărca o imagine: {e}')
            
            messages.success(request, 'Anunțul a fost creat cu succes!')
            return redirect('listings:detail', slug=listing.slug)
    else:
        form = ListingForm()
    
    context = {
        'form': form,
        'title': 'Adaugă anunț nou'
    }
    return render(request, 'listings/create_simple.html', context)

@login_required
def listing_update_view(request, slug):
    """Editează un anunț"""
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        form = ListingForm(request.POST, instance=listing)
        formset = ListingImageFormSet(request.POST, request.FILES, queryset=listing.images.all())
        
        if form.is_valid() and formset.is_valid():
            listing = form.save()
            
            # Procesează imaginile
            for image_form in formset:
                if image_form.cleaned_data:
                    if image_form.cleaned_data.get('DELETE', False):
                        if image_form.instance.pk:
                            image_form.instance.delete()
                    elif image_form.cleaned_data.get('image'):
                        image = image_form.save(commit=False)
                        image.listing = listing
                        image.save()
            
            messages.success(request, 'Anunțul a fost actualizat!')
            return redirect('listings:detail', slug=listing.slug)
    else:
        form = ListingForm(instance=listing)
        formset = ListingImageFormSet(queryset=listing.images.all())
    
    context = {
        'form': form,
        'formset': formset,
        'listing': listing,
        'title': f'Editează: {listing.title}'
    }
    return render(request, 'listings/update.html', context)

@login_required
def listing_delete_view(request, slug):
    """Șterge un anunț"""
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Anunțul a fost șters!')
        return redirect('listings:my_listings')
    
    context = {'listing': listing}
    return render(request, 'listings/delete.html', context)

@login_required
def my_listings_view(request):
    """Anunțurile mele"""
    listings = Listing.objects.filter(owner=request.user).order_by('-created_at')
    
    paginator = Paginator(listings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'listings/my_listings.html', context)

@login_required
def upload_images_view(request, slug):
    """Upload imagini pentru anunț"""
    listing = get_object_or_404(Listing, slug=slug, owner=request.user)
    
    if request.method == 'POST':
        formset = ListingImageFormSet(request.POST, request.FILES, queryset=listing.images.all())
        
        if formset.is_valid():
            for image_form in formset:
                if image_form.cleaned_data and not image_form.cleaned_data.get('DELETE', False):
                    if image_form.cleaned_data.get('image'):  # Doar dacă există imagine nouă
                        image = image_form.save(commit=False)
                        image.listing = listing
                        image.save()
            
            messages.success(request, 'Imaginile au fost încărcate!')
            return redirect('listings:detail', slug=listing.slug)
    else:
        # Formset cu imagini existente plus 3 forme goale
        formset = ListingImageFormSet(queryset=listing.images.all())
    
    context = {
        'listing': listing,
        'formset': formset,
        'title': f'Imagini pentru: {listing.title}'
    }
    return render(request, 'listings/upload_images.html', context)