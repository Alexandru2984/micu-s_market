from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Conversation, Message, MessageAttachment
from listings.models import Listing

User = get_user_model()

@login_required
def inbox_view(request):
    """Inbox-ul cu toate conversațiile utilizatorului"""
    conversations = Conversation.objects.filter(
        participants=request.user,
        is_active=True
    ).select_related('listing').prefetch_related('participants', 'messages').annotate(
        unread_count=Count('messages', filter=Q(messages__receiver=request.user, messages__is_read=False))
    ).order_by('-updated_at')
    
    # Adaugă celălalt participant la fiecare conversație
    for conversation in conversations:
        conversation.other_participant = conversation.get_other_participant(request.user)
    
    # Paginare
    paginator = Paginator(conversations, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_unread': sum(conv.unread_count for conv in conversations)
    }
    return render(request, 'chat/inbox.html', context)

@login_required
def conversation_view(request, pk):
    """View pentru o conversație specifică"""
    conversation = get_object_or_404(
        Conversation.objects.select_related('listing').prefetch_related('participants'),
        pk=pk,
        participants=request.user
    )
    
    # Marchează mesajele ca citite
    conversation.mark_as_read(request.user)
    
    # Obține mesajele
    messages_list = conversation.messages.select_related('sender', 'receiver').prefetch_related('attachments').order_by('created_at')
    
    # Paginare pentru mesaje
    paginator = Paginator(messages_list, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Celălalt participant
    other_participant = conversation.get_other_participant(request.user)
    
    context = {
        'conversation': conversation,
        'page_obj': page_obj,
        'other_participant': other_participant,
        'listing': conversation.listing
    }
    return render(request, 'chat/conversation.html', context)

@login_required
def start_conversation_view(request, listing_slug):
    """Începe o conversație nouă despre un anunț"""
    try:
        listing = get_object_or_404(Listing, slug=listing_slug, status='active')
        
        # Debug info
        print(f"DEBUG: User {request.user} wants to chat about listing '{listing.title}' owned by {listing.owner}")
        
        # Nu permite utilizatorului să înceapă conversație cu sine însuși
        if listing.owner == request.user:
            messages.error(request, "Nu poți începe o conversație cu tine însuți.")
            return redirect('listings:detail', slug=listing_slug)
        
        # Verifică dacă există deja o conversație
        existing_conversation = Conversation.objects.filter(
            listing=listing,
            participants=request.user
        ).filter(participants=listing.owner).first()
        
        if existing_conversation:
            messages.info(request, "Conversația există deja!")
            return redirect('chat:conversation', pk=existing_conversation.pk)
        
        # Creează conversația nouă
        conversation = Conversation.objects.create(listing=listing)
        conversation.participants.add(request.user, listing.owner)
        
        # Mesaj de welcome automat
        welcome_message = f"Salut! Sunt interessat de anunțul tău '{listing.title}'."
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            receiver=listing.owner,
            content=welcome_message
        )
        
        messages.success(request, f"Conversația despre '{listing.title}' a fost începută cu succes!")
        return redirect('chat:conversation', pk=conversation.pk)
        
    except Exception as e:
        print(f"ERROR in start_conversation_view: {e}")
        messages.error(request, f"Eroare la începerea conversației: {e}")
        return redirect('listings:detail', slug=listing_slug)

@login_required
@require_POST
def send_message_view(request, conversation_pk):
    """Trimite un mesaj într-o conversație"""
    conversation = get_object_or_404(
        Conversation,
        pk=conversation_pk,
        participants=request.user
    )
    
    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'error': 'Mesajul nu poate fi gol.'}, status=400)
    
    # Determină destinatarul
    receiver = conversation.get_other_participant(request.user)
    
    # Creează mesajul
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        receiver=receiver,
        content=content
    )
    
    # Procesează atașamentele dacă există
    if 'attachments' in request.FILES:
        for file in request.FILES.getlist('attachments'):
            MessageAttachment.objects.create(
                message=message,
                file=file
            )
    
    # Returnează răspunsul JSON pentru AJAX
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
                        'url': att.file.url,
                        'filename': att.filename,
                        'file_type': att.file_type
                    } for att in message.attachments.all()
                ]
            }
        })
    
    return redirect('chat:conversation', pk=conversation_pk)

@login_required
def search_users_view(request):
    """Caută utilizatori pentru a începe o conversație"""
    query = request.GET.get('q', '').strip()
    users = []
    
    if query and len(query) >= 2:
        users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query)
        ).exclude(id=request.user.id)[:10]
    
    users_data = [
        {
            'id': user.id,
            'username': user.username,
            'display_name': user.get_full_name() or user.username,
            'avatar': user.profile.avatar.url if hasattr(user, 'profile') and user.profile.avatar else None
        }
        for user in users
    ]
    
    return JsonResponse({'users': users_data})

@login_required
def get_unread_count(request):
    """Returnează numărul de mesaje necitite"""
    count = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'unread_count': count})

@login_required
def mark_conversation_read(request, pk):
    """Marchează o conversație ca citită"""
    conversation = get_object_or_404(
        Conversation,
        pk=pk,
        participants=request.user
    )
    
    conversation.mark_as_read(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('chat:conversation', pk=pk)
