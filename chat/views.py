import logging
import mimetypes

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import FileResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django_ratelimit.decorators import ratelimit

from listings.models import Listing
from notifications.models import Notification

from .broadcast import broadcast_message
from .models import Conversation, Message, MessageAttachment
from .validators import MAX_ATTACHMENTS_PER_MESSAGE, is_allowed_chat_attachment

logger = logging.getLogger(__name__)
User = get_user_model()

@login_required
def inbox_view(request):
    """Inbox with all of the user's conversations"""
    conversations = Conversation.objects.filter(
        participants=request.user,
        is_active=True
    ).select_related('listing').prefetch_related('participants', 'messages').annotate(
        unread_count=Count('messages', filter=Q(messages__receiver=request.user, messages__is_read=False))
    ).order_by('-updated_at')
    
    # Add the other participant to each conversation
    for conversation in conversations:
        conversation.other_participant = conversation.get_other_participant(request.user)
    
    # Paginare
    paginator = Paginator(conversations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Total unread messages — a single direct query (don't iterate all conversations)
    total_unread = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    
    context = {
        'page_obj': page_obj,
        'total_unread': total_unread
    }
    return render(request, 'chat/inbox.html', context)

@login_required
def conversation_view(request, pk):
    """View for a specific conversation"""
    conversation = get_object_or_404(
        Conversation.objects.select_related('listing').prefetch_related('participants'),
        pk=pk,
        participants=request.user
    )
    
    # Mark messages as read
    conversation.mark_as_read(request.user)
    
    # Get the messages
    messages_list = conversation.messages.select_related('sender', 'receiver').prefetch_related('attachments').order_by('created_at')
    
    # Paginate the messages
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # The other participant
    other_participant = conversation.get_other_participant(request.user)
    
    context = {
        'conversation': conversation,
        'page_obj': page_obj,
        'other_participant': other_participant,
        'listing': conversation.listing
    }
    return render(request, 'chat/conversation.html', context)

@login_required
@require_POST
@ratelimit(key='user', rate=settings.CHAT_START_RATE, method='POST', block=True)
def start_conversation_view(request, listing_slug):
    """Start a new conversation about a listing"""
    try:
        listing = get_object_or_404(Listing, slug=listing_slug, status='active')
        
        # Debug info (log server-side, not in the browser)
        logger.debug("User %s vrea să contacteze proprietarul anunțului '%s' (owner: %s)",
                     request.user, listing.title, listing.owner)
        
        # Don't allow the user to start a conversation with themselves
        if listing.owner == request.user:
            messages.error(request, "Nu poți începe o conversație cu tine însuți.")
            return redirect('listings:detail', slug=listing_slug)
        
        # Check if a conversation already exists
        existing_conversation = Conversation.objects.filter(
            listing=listing,
            participants=request.user
        ).filter(participants=listing.owner).first()
        
        if existing_conversation:
            messages.info(request, "Conversația există deja!")
            return redirect('chat:conversation', pk=existing_conversation.pk)
        
        # Create the new conversation
        conversation = Conversation.objects.create(listing=listing)
        conversation.participants.add(request.user, listing.owner)
        
        # Automatic welcome message
        welcome_message = f"Salut! Sunt interesat de anunțul tău '{listing.title}'."
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            receiver=listing.owner,
            content=welcome_message
        )
        
        messages.success(request, f"Conversația despre '{listing.title}' a fost începută cu succes!")
        return redirect('chat:conversation', pk=conversation.pk)
        
    except Exception:
        logger.exception("Eroare în start_conversation_view pentru user=%s, listing=%s",
                         request.user, listing_slug)
        messages.error(request, "A apărut o eroare. Te rugăm încearcă din nou.")
        return redirect('listings:detail', slug=listing_slug)

@login_required
@require_POST
@ratelimit(key='user', rate='60/m', block=True)
def send_message_view(request, conversation_pk):
    """Send a message in a conversation"""
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_pk,
        participants=request.user
    )
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Mesajul nu poate fi gol.'}, status=400)
    if len(content) > settings.CHAT_MESSAGE_MAX_LENGTH:
        return JsonResponse({'error': 'Mesajul este prea lung.'}, status=400)
    
    # Determine the recipient
    receiver = conversation.get_other_participant(request.user)
    
    # Create the message
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        receiver=receiver,
        content=content
    )
    Notification.objects.create(
        recipient=receiver,
        notification_type="new_message",
        title="Mesaj nou",
        message=f"{request.user.get_full_name() or request.user.username} ți-a trimis un mesaj.",
        related_object_type="Conversation",
        related_object_id=conversation.pk,
        action_url=conversation.get_absolute_url(),
    )
    
    # Process attachments with server-side validation.
    if 'attachments' in request.FILES:
        uploaded_files = request.FILES.getlist('attachments')[:MAX_ATTACHMENTS_PER_MESSAGE]
        for file in uploaded_files:
            if is_allowed_chat_attachment(file):
                MessageAttachment.objects.create(message=message, file=file)

    # Broadcast live to the other participant (connected over WebSocket). The
    # sender's own client de-duplicates by id, so it isn't shown twice vs the AJAX response.
    broadcast_message(message)

    # Return the JSON response for AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'created_at': message.created_at.strftime('%H:%M'),
                'attachments': [
                    {
                        'url': att.download_url,
                        'download_url': att.download_url,
                        'filename': att.filename,
                        'file_type': att.file_type
                    } for att in message.attachments.all()
                ]
            }
        })
    
    return redirect('chat:conversation', pk=conversation_pk)

@login_required
@require_GET
@ratelimit(key='user', rate=settings.SENSITIVE_READ_RATE, method='GET', block=True)
def search_users_view(request):
    """Search users to start a conversation"""
    query = request.GET.get('q', '').strip()
    users = []
    
    if query and len(query) >= 2:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10]
    
    # Don't expose internal user IDs
    users_data = [
        {
            'username': user.username,
            'display_name': user.get_full_name() or user.username,
            'avatar': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else None
        }
        for user in users
    ]
    
    return JsonResponse({'users': users_data})

@login_required
@require_GET
@ratelimit(key='user', rate=settings.SENSITIVE_READ_RATE, method='GET', block=True)
def get_unread_count(request):
    """Return the unread message count"""
    count = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'unread_count': count})

@login_required
@require_GET
def attachment_download_view(request, pk):
    """Serve attachments only to conversation participants."""
    attachment = get_object_or_404(
        MessageAttachment.objects.select_related('message__conversation'),
        pk=pk,
        message__conversation__participants=request.user,
    )
    content_type, _ = mimetypes.guess_type(attachment.filename)
    response = FileResponse(
        attachment.file.open('rb'),
        as_attachment=attachment.file_type != 'image',
        filename=attachment.filename,
        content_type=content_type or 'application/octet-stream',
    )
    response['Cache-Control'] = 'private, no-store'
    response['Pragma'] = 'no-cache'
    response['X-Content-Type-Options'] = 'nosniff'
    return response

@login_required
@require_POST
def mark_conversation_read(request, pk):
    """Mark a conversation as read"""
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
        participants=request.user
    )
    
    conversation.mark_as_read(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('chat:conversation', pk=pk)
