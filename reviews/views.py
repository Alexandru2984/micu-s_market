from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.conf import settings
from django_ratelimit.decorators import ratelimit


from .models import Review, ReviewResponse
from listings.models import Listing
from .forms import ReviewForm, ReviewResponseForm
from chat.models import Conversation

User = get_user_model()


def _can_review_transaction(reviewer, reviewed_user, listing=None):
    conversations = Conversation.objects.filter(
        participants=reviewer,
        is_active=True,
    ).filter(participants=reviewed_user)
    if listing is not None:
        conversations = conversations.filter(listing=listing)
    return conversations.exists()

def user_reviews_view(request, username):
    """Display all reviews for a user"""
    user = get_object_or_404(User, username=username)

    # Fetch the reviews for the user
    reviews = Review.objects.filter(
        reviewed_user=user,
        is_approved=True
    ).select_related('reviewer', 'listing').prefetch_related('response').order_by('-created_at')
    
    # Statistics
    total_reviews = reviews.count()
    if total_reviews > 0:
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        rating_distribution = {
            5: reviews.filter(rating=5).count(),
            4: reviews.filter(rating=4).count(),
            3: reviews.filter(rating=3).count(),
            2: reviews.filter(rating=2).count(),
            1: reviews.filter(rating=1).count(),
        }
    else:
        avg_rating = 0
        rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    
    # Pagination
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reviewed_user': user,
        'page_obj': page_obj,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'rating_distribution': rating_distribution,
    }
    return render(request, 'reviews/user_reviews.html', context)

@login_required
@ratelimit(key='user', rate='5/h', method='POST', block=True)
def create_review_view(request, username, listing_slug=None):
    """Create a review for a user"""
    reviewed_user = get_object_or_404(User, username=username)
    listing = None
    
    listing_slug = listing_slug or request.GET.get('listing')
    if listing_slug:
        listing = get_object_or_404(Listing, slug=listing_slug)
        if listing.owner_id != reviewed_user.id:
            messages.error(request, "Review-ul nu poate fi atașat la un anunț care aparține altui utilizator.")
            return redirect('accounts:public_profile', username=username)
    
    # You cannot leave a review for yourself
    if reviewed_user == request.user:
        messages.error(request, "Nu poți lăsa un review pentru tine însuți.")
        return redirect('accounts:public_profile', username=username)

    # Check whether a review already exists for this combination
    existing_review = Review.objects.filter(
        reviewer=request.user,
        reviewed_user=reviewed_user,
        listing=listing
    ).first()
    
    if existing_review:
        messages.warning(request, "Ai lăsat deja un review pentru acest utilizator/anunț.")
        return redirect('reviews:user_reviews', username=username)

    if not _can_review_transaction(request.user, reviewed_user, listing):
        messages.error(
            request,
            "Poți lăsa review doar după o conversație relevantă cu acest utilizator.",
        )
        return redirect('accounts:public_profile', username=username)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.reviewer = request.user
            review.reviewed_user = reviewed_user
            review.listing = listing
            review.save()
            
            messages.success(request, "Review-ul a fost adăugat cu succes!")
            return redirect('reviews:user_reviews', username=username)
    else:
        initial_data = {}
        if listing:
            initial_data['title'] = f"Experiența cu anunțul '{listing.title}'"
        form = ReviewForm(initial=initial_data)
    
    context = {
        'form': form,
        'reviewed_user': reviewed_user,
        'listing': listing,
    }
    return render(request, 'reviews/create.html', context)

@login_required
def add_response_view(request, review_id):
    """Add a response to a review"""
    review = get_object_or_404(Review, id=review_id, reviewed_user=request.user)

    # Check whether a response already exists
    if hasattr(review, 'response'):
        messages.warning(request, "Ai răspuns deja la acest review.")
        return redirect('reviews:user_reviews', username=request.user.username)
    
    if request.method == 'POST':
        form = ReviewResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.review = review
            response.save()
            
            messages.success(request, "Răspunsul a fost adăugat cu succes!")
            return redirect('reviews:user_reviews', username=request.user.username)
    else:
        form = ReviewResponseForm()
    
    context = {
        'form': form,
        'review': review,
    }
    return render(request, 'reviews/add_response.html', context)

@login_required
def edit_review_view(request, review_id):
    """Edit a review"""
    review = get_object_or_404(Review, id=review_id, reviewer=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review-ul a fost actualizat cu succes!")
            return redirect('reviews:user_reviews', username=review.reviewed_user.username)
    else:
        form = ReviewForm(instance=review)
    
    context = {
        'form': form,
        'review': review,
        'is_edit': True,
    }
    return render(request, 'reviews/create.html', context)

@login_required
@require_POST
def delete_review_view(request, review_id):
    """Delete a review"""
    review = get_object_or_404(Review, id=review_id, reviewer=request.user)
    username = review.reviewed_user.username
    review.delete()
    
    messages.success(request, "Review-ul a fost șters cu succes!")
    return redirect('reviews:user_reviews', username=username)

@require_GET
@ratelimit(key='ip', rate=settings.SENSITIVE_READ_RATE, method='GET', block=True)
def reviews_stats_api(request, username):
    """API for review statistics"""
    user = get_object_or_404(User, username=username)
    
    reviews = Review.objects.filter(reviewed_user=user, is_approved=True)
    total_reviews = reviews.count()
    
    if total_reviews > 0:
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg']
        rating_distribution = {
            str(i): reviews.filter(rating=i).count() for i in range(1, 6)
        }
    else:
        avg_rating = 0
        rating_distribution = {str(i): 0 for i in range(1, 6)}
    
    return JsonResponse({
        'total_reviews': total_reviews,
        'average_rating': round(avg_rating, 1) if avg_rating else 0,
        'rating_distribution': rating_distribution
    })

@login_required
def my_reviews_view(request):
    """The reviews I have written"""
    reviews = Review.objects.filter(
        reviewer=request.user
    ).select_related('reviewed_user', 'listing').order_by('-created_at')
    
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'reviews/my_reviews.html', context)
