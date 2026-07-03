from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit

from audit.utils import audit_log
from listings.models import Listing

from .forms import CustomAuthenticationForm, CustomUserCreationForm, UserProfileForm, UserReportForm
from .models import UserProfile, UserReport

User = get_user_model()

@ratelimit(key='ip', rate=settings.AUTH_REGISTER_RATE, method='POST', block=True)
@sensitive_post_parameters('password1', 'password2')
def register_view(request):
    """Register a new user"""
    if request.user.is_authenticated:
        return redirect('listings:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Contul pentru {username} a fost creat cu succes! Te poți autentifica acum.')
            return redirect('accounts:login')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'account/signup.html', {'form': form})

@ratelimit(key='ip', rate=settings.AUTH_LOGIN_IP_RATE, method='POST', block=True)
@ratelimit(key='post:username', rate=settings.AUTH_LOGIN_USER_RATE, method='POST', block=True)
@sensitive_post_parameters('password')
def login_view(request):
    """Authenticate a user"""
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
    """Log the user out — accepts POST only to prevent CSRF force-logout"""
    actor = request.user if request.user.is_authenticated else None
    audit_log("auth.logout", request=request, actor=actor)
    logout(request)
    messages.info(request, 'Te-ai deconectat cu succes!')
    return redirect('listings:home')

@login_required
def profile_view(request):
    """The current user's profile"""
    from django.db.models import Q
    # Make sure the user has a profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    # Compute statistics in a single aggregate query
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
    """Edit the user's profile"""
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
    """Submit the user's profile for manual verification."""
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
    """A user's public profile"""
    user = get_object_or_404(User, username=username)

    # Do not auto-create profiles in public GET views
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        profile = None

    # The user's active listings
    listings = Listing.objects.filter(owner=user, status='active').order_by('-created_at')[:6]

    # Public statistics — a single query
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

# my_listings_view was moved to listings/views.py (the canonical version with status filtering)
# The accounts:my_listings URL can redirect there if needed
