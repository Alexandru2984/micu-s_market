from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.cache import cache
from django_ratelimit.decorators import ratelimit
import logging
import hashlib
from decimal import Decimal, InvalidOperation
from .models import Listing, ListingImage, ListingReport
from .forms import ListingForm, ListingImageForm, ListingImageFormSet, ListingReportForm
from .search import apply_listing_search, order_search_results
from .moderation import apply_listing_risk_review
from categories.models import Category
from favorites.models import Favorite
from audit.utils import audit_log
from notifications.models import Notification

logger = logging.getLogger(__name__)


def _listing_view_cache_key(request, listing_id):
    if request.user.is_authenticated:
        actor = f"user:{request.user.pk}"
    else:
        remote_addr = request.META.get("REMOTE_ADDR", "")
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        actor_hash = hashlib.sha256(f"{remote_addr}:{user_agent}".encode("utf-8")).hexdigest()
        actor = f"anon:{actor_hash}"
    return f"listing:{listing_id}:viewed:{actor}"


def _parse_price_filter(raw_value):
    if raw_value in (None, ""):
        return None
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError):
        return None
    return value if value >= 0 else None

def home_view(request):
    """Homepage cu anunțuri recente și categorii"""
    recent_listings = Listing.objects.filter(status='active').select_related('category', 'owner').prefetch_related('images').order_by('-created_at')[:8]
    now = timezone.now()
    featured_listings = (
        Listing.objects.filter(status='active', is_featured=True)
        .filter(Q(featured_until__isnull=True) | Q(featured_until__gt=now))
        .select_related('category', 'owner')
        .prefetch_related('images')
        .order_by('-created_at')[:4]
    )
    
    # Adăugă starea de favorite pentru utilizatorul autentificat
    if request.user.is_authenticated:
        user_favorites = set(Favorite.objects.filter(user=request.user).values_list('listing_id', flat=True))
        
        for listing in recent_listings:
            listing.is_favorited = listing.id in user_favorites
        for listing in featured_listings:
            listing.is_favorited = listing.id in user_favorites
    
    # Categorii cu număr de anunțuri — un singur query agregat (fix N+1)
    # Folosim annotate pentru a obține numărul de anunțuri active per categorie
    top_categories = cache.get("home:top_categories")
    if top_categories is None:
        categories_with_counts = (
            Category.objects.filter(is_active=True)
            .annotate(
                active_listings_count=Count(
                    'listings',
                    filter=Q(listings__status='active'),
                    distinct=True
                )
            )
            .order_by('-active_listings_count', 'order', 'name')
        )
        top_categories = list(categories_with_counts[:12])
        cache.set("home:top_categories", top_categories, settings.HOMEPAGE_CACHE_SECONDS)
    
    context = {
        'recent_listings': recent_listings,
        'featured_listings': featured_listings,
        'categories': top_categories,
    }
    return render(request, 'listings/home.html', context)

def listing_list_view(request):
    """Lista anunțurilor cu filtrare și sortare"""
    listings = Listing.objects.filter(status='active').select_related('category', 'owner').prefetch_related('images')
    
    # Filtrare după vânzător
    seller = request.GET.get('seller')
    if seller:
        listings = listings.filter(owner__username=seller)
    
    # Filtrare după categorie
    category_param = request.GET.get('category')
    selected_category = None
    if category_param:
        try:
            # Încearcă să găsească categoria după slug
            selected_category = Category.objects.get(slug=category_param, is_active=True)
            # Include categoria principală și toate subcategoriile
            category_ids = [selected_category.id] + [sub.id for sub in selected_category.get_all_children]
            listings = listings.filter(category_id__in=category_ids)
        except Category.DoesNotExist:
            # Dacă nu găsește după slug, încearcă după ID
            try:
                selected_category = Category.objects.get(id=category_param, is_active=True)
                # Include categoria principală și toate subcategoriile
                category_ids = [selected_category.id] + [sub.id for sub in selected_category.get_all_children]
                listings = listings.filter(category_id__in=category_ids)
            except (Category.DoesNotExist, ValueError):
                # Dacă nu găsește nici după ID, ignoră filtrul
                pass
    
    # Filtrare după preț
    min_price = _parse_price_filter(request.GET.get('min_price'))
    max_price = _parse_price_filter(request.GET.get('max_price'))
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
    listings, search_applied = apply_listing_search(listings, search)
    
    # Sortare
    sort_by = request.GET.get('sort', 'relevance' if search_applied else '-created_at')
    valid_sorts = ['relevance', '-created_at', 'created_at', 'price', '-price', 'title', '-title']
    if sort_by in valid_sorts:
        listings = order_search_results(listings, sort_by, search_applied)
        if sort_by != 'relevance':
            listings = listings.order_by(sort_by)
    else:
        listings = listings.order_by('-created_at')
    
    # Paginare
    paginator = Paginator(listings, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Adăugă starea de favorite pentru utilizatorul autentificat
    if request.user.is_authenticated:
        user_favorites = set(Favorite.objects.filter(user=request.user).values_list('listing_id', flat=True))
        
        for listing in page_obj:
            listing.is_favorited = listing.id in user_favorites
    
    # Context pentru template
    categories = Category.objects.filter(is_active=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_category': selected_category,
        'current_category_slug': category_param,
        'current_city': city,
        'current_seller': seller,
        'min_price': min_price,
        'max_price': max_price,
        'search_query': search,
        'sort_by': sort_by,
    }
    return render(request, 'listings/list.html', context)

def listing_detail_view(request, slug):
    """Detaliile unui anunț"""
    listing = get_object_or_404(Listing, slug=slug, status='active')
    
    view_cache_key = _listing_view_cache_key(request, listing.pk)
    if cache.add(view_cache_key, True, settings.LISTING_VIEW_COOLDOWN_SECONDS):
        Listing.objects.filter(pk=listing.pk).update(views_count=F('views_count') + 1)
        listing.views_count += 1
    
    # Verifică dacă anunțul este în favorite pentru utilizatorul autentificat
    is_favorited = False
    if request.user.is_authenticated:

        is_favorited = Favorite.objects.filter(user=request.user, listing=listing).exists()
    
    # Anunțuri similare
    similar_listings = Listing.objects.filter(
        category=listing.category,
        status='active'
    ).exclude(id=listing.id).prefetch_related('images')[:4]
    
    context = {
        'listing': listing,
        'similar_listings': similar_listings,
        'is_favorited': is_favorited,
        'report_form': ListingReportForm(),
    }
    return render(request, 'listings/detail.html', context)


@login_required
@require_POST
@ratelimit(key='user', rate=settings.REPORT_WRITE_RATE, method='POST', block=True)
def report_listing_view(request, slug):
    """Creează un raport de moderare pentru un anunț."""
    listing = get_object_or_404(Listing, slug=slug, status='active')

    if listing.owner == request.user:
        messages.error(request, "Nu poți raporta propriul anunț.")
        return redirect('listings:detail', slug=listing.slug)

    active_report_exists = ListingReport.objects.filter(
        listing=listing,
        reporter=request.user,
        status__in=["pending", "reviewed"],
    ).exists()
    if active_report_exists:
        messages.info(request, "Ai deja un raport activ pentru acest anunț.")
        return redirect('listings:detail', slug=listing.slug)

    form = ListingReportForm(request.POST)
    listing_hidden = False
    if form.is_valid():
        report = form.save(commit=False)
        report.listing = listing
        report.reporter = request.user
        report.save()
        audit_log("listing.report", request=request, obj=listing, metadata={"report_id": report.pk, "reason": report.reason})
        active_reports = ListingReport.objects.filter(
            listing=listing,
            status__in=["pending", "reviewed"],
        ).count()
        if active_reports >= settings.LISTING_AUTO_HIDE_REPORT_THRESHOLD and listing.status == "active":
            listing.status = "inactive"
            listing.save(update_fields=["status", "updated_at"])
            listing_hidden = True
            Notification.objects.create(
                recipient=listing.owner,
                notification_type="listing_rejected",
                title="Anunț ascuns temporar",
                message="Anunțul tău a fost ascuns temporar pentru moderare după mai multe rapoarte.",
                related_object_type="Listing",
                related_object_id=listing.pk,
                action_url=listing.get_absolute_url(),
            )
        messages.success(request, "Raportul a fost trimis către moderare.")
    else:
        messages.error(request, "Raportul nu a putut fi trimis. Verifică motivul selectat.")

    if listing_hidden:
        return redirect('listings:list')
    return redirect('listings:detail', slug=listing.slug)

def process_images(request, listing):
    """Procesează și salvează imaginile pentru un anunț (maxim 10)"""
    images = request.FILES.getlist('images')
    
    # Limită server-side (nu depăşete formset max_num=10)
    if len(images) > 10:
        images = images[:10]
    for image in images:
        if image:
            image_form = ListingImageForm(files={'image': image})
            if not image_form.is_valid():
                messages.warning(request, 'Nu am putut încărca o imagine. Verifică formatul şi dimensiunea.')
                continue

            try:
                listing_image = image_form.save(commit=False)
                listing_image.listing = listing
                listing_image.alt_text = f"Imagine pentru {listing.title}"
                listing_image.save()
            except Exception:
                logger.exception("Eroare la încărcarea imaginii pentru anunțul %s", listing.pk)
                messages.warning(request, 'Nu am putut încărca o imagine. Verifică formatul şi dimensiunea.')

@login_required
@ratelimit(key='user', rate='10/h', method='POST', block=True)
def listing_create_view(request):
    """Creează anunț nou"""
    if request.method == 'POST':
        form = ListingForm(request.POST)
        
        if form.is_valid():
            listing = form.save(commit=False)
            listing.owner = request.user
            listing.save()
            apply_listing_risk_review(listing, request.user, request=request)
            
            # Folosește funcția auxiliară
            process_images(request, listing)

            if listing.needs_moderation_review:
                messages.warning(request, "Anunțul a fost trimis la moderare înainte de publicare.")
                return redirect('listings:my_listings')
            
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
            apply_listing_risk_review(listing, request.user, request=request)
            formset.save() # Aceasta se va ocupa de salvarea/ștergerea imaginilor

            if listing.needs_moderation_review:
                messages.warning(request, "Anunțul a fost trimis la moderare înainte de republicare.")
                return redirect('listings:my_listings')
            
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
