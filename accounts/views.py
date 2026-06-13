from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from .forms import CustomUserCreationForm, CustomAuthenticationForm, UserProfileForm, UserReportForm
from .models import UserProfile, UserReport
from listings.models import Listing
from audit.utils import audit_log

User = get_user_model()

def register_view(request):
    """Înregistrare utilizator nou"""
    if request.user.is_authenticated:
        return redirect('listings:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Contul pentru {username} a fost creat cu succes! Te poți autentifica acum.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'account/signup.html', {'form': form})

def login_view(request):
    """Autentificare utilizator"""
    if request.user.is_authenticated:
        return redirect('listings:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next')
                if not url_has_allowed_host_and_scheme(
                    url=next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                ):
                    next_url = reverse('listings:home')
                messages.success(request, f'Bine ai venit, {user.get_full_name() or user.username}!')
                audit_log("auth.login", request=request, actor=user)
                return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'account/login.html', {'form': form})

@require_POST
def logout_view(request):
    """Deconectare utilizator — acceptă doar POST pentru a preveni CSRF force-logout"""
    actor = request.user if request.user.is_authenticated else None
    audit_log("auth.logout", request=request, actor=actor)
    logout(request)
    messages.info(request, 'Te-ai deconectat cu succes!')
    return redirect('listings:home')

@login_required
def profile_view(request):
    """Profilul utilizatorului curent"""
    from django.db.models import Q
    # Asigură-te că utilizatorul are un profil
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Calculează statistici într-un singur query agregat
    stats_qs = Listing.objects.filter(owner=request.user).aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='active')),
        sold=Count('id', filter=Q(status='sold')),
    )
    
    user_stats = {
        'total_listings': stats_qs['total'],
        'active_listings': stats_qs['active'],
        'sold_listings': stats_qs['sold'],
        'member_since': request.user.date_joined,
    }
    
    context = {
        'profile': profile,
        'user_stats': user_stats,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def profile_edit_view(request):
    """Editează profilul utilizatorului"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profilul a fost actualizat cu succes!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=profile, user=request.user)
    
    context = {
        'form': form,
        'profile': profile,
    }
    return render(request, 'accounts/profile_edit.html', context)


@login_required
@require_POST
def request_verification_view(request):
    """Trimite profilul utilizatorului către verificare manuală."""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if profile.is_verified:
        messages.info(request, 'Profilul este deja verificat.')
    elif profile.verification_status == "pending":
        messages.info(request, 'Cererea ta de verificare este deja în analiză.')
    elif profile.request_verification():
        messages.success(request, 'Cererea de verificare a fost trimisă.')
        audit_log("profile.verification_requested", request=request, obj=profile)
    else:
        messages.error(request, 'Cererea de verificare nu a putut fi trimisă.')

    return redirect('accounts:profile')

def public_profile_view(request, username):
    """Profilul public al unui utilizator"""
    user = get_object_or_404(User, username=username)
    
    # Nu auto-crea profiluri în view-uri GET publice
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = None
    
    # Anunțurile active ale utilizatorului
    listings = Listing.objects.filter(owner=user, status='active').order_by('-created_at')[:6]
    
    # Statistici publice — un singur query
    from django.db.models import Q
    stats_qs = Listing.objects.filter(owner=user).aggregate(
        total=Count('id', filter=Q(status='active')),
    )
    
    user_stats = {
        'total_listings': stats_qs['total'],
        'member_since': user.date_joined,
        'average_rating': profile.average_rating if profile else 0,
    }
    
    context = {
        'profile_user': user,
        'profile': profile,
        'listings': listings,
        'user_stats': user_stats,
        'report_form': UserReportForm(),
    }
    return render(request, 'accounts/public_profile.html', context)


@login_required
@require_POST
@ratelimit(key='user', rate=settings.REPORT_WRITE_RATE, method='POST', block=True)
def report_user_view(request, username):
    reported_user = get_object_or_404(User, username=username)
    if reported_user == request.user:
        messages.error(request, 'Nu îți poți raporta propriul profil.')
        return redirect('accounts:public_profile', username=username)

    active_exists = UserReport.objects.filter(
        reported_user=reported_user,
        reporter=request.user,
        status__in=["pending", "reviewed"],
    ).exists()
    if active_exists:
        messages.info(request, 'Ai deja un raport activ pentru acest utilizator.')
        return redirect('accounts:public_profile', username=username)

    form = UserReportForm(request.POST)
    if form.is_valid():
        report = form.save(commit=False)
        report.reported_user = reported_user
        report.reporter = request.user
        report.save()
        messages.success(request, 'Raportul a fost trimis către moderare.')
    else:
        messages.error(request, 'Raportul nu a putut fi trimis.')

    return redirect('accounts:public_profile', username=username)

# my_listings_view a fost mutat în listings/views.py (versiunea canonică cu filtrare status)
# URL-ul accounts:my_listings poate redirecta acolo dacă e nevoie
