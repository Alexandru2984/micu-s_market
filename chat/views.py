from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django_ratelimit.decorators import ratelimit
import json
import logging

from .models import Conversation, Message, MessageAttachment
from listings.models import Listing

logger = logging.getLogger(__name__)
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
    
    # Total mesaje necitite — un singur query direct (nu itera toate conversațiile)
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
@require_POST
def start_conversation_view(request, listing_slug):
    """Începe o conversație nouă despre un anunț"""
    try:
        listing = get_object_or_404(Listing, slug=listing_slug, status='active')
        
        # Debug info (log server-side, nu în browser)
        logger.debug("User %s vrea să contacteze proprietarul anunțului '%s' (owner: %s)",
                     request.user, listing.title, listing.owner)
        
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
        logger.exception("Eroare în start_conversation_view pentru user=%s, listing=%s",
                         request.user, listing_slug)
        messages.error(request, "A apărut o eroare. Te rugăm încearcă din nou.")
        return redirect('listings:detail', slug=listing_slug)

@login_required
@require_POST
@ratelimit(key='user', rate='60/m', block=True)
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
    
    # Procesează atașamentele cu validare completă
    if 'attachments' in request.FILES:
        ALLOWED_EXTENSIONS = {
            'jpg', 'jpeg', 'png', 'gif', 'webp',  # imagini
            'pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx',  # documente
        }
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per fișier
        MAX_FILES = 5  # maxim 5 atașamente per mesaj

        uploaded_files = request.FILES.getlist('attachments')[:MAX_FILES]  # ignoră restul

        for file in uploaded_files:
            # Verifică extensia
            ext = file.name.rsplit('.', 1)[-1].lower() if '.' in file.name else ''
            if ext not in ALLOWED_EXTENSIONS:
                continue  # sări fișierele cu extensii nepermise

            # Verifică dimensiunea
            if file.size > MAX_FILE_SIZE:
                continue  # sări fișierele prea mari

            # Verifică conținutul imaginilor cu Pillow
            if ext in {'jpg', 'jpeg', 'png', 'gif', 'webp'}:
                try:
                    from PIL import Image as PilImage
                    file.seek(0)
                    img = PilImage.open(file)
                    img.verify()
                    file.seek(0)
                except Exception:
                    continue  # fișier imagine invalid/fals

            MessageAttachment.objects.create(message=message, file=file)
    
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
    
    # Nu expunăm ID-urile interne ale utilizatorilor
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
def get_unread_count(request):
    """Returnează numărul de mesaje necitite"""
    count = Message.objects.filter(
        receiver=request.user,
        is_read=False
    ).count()
    
    return JsonResponse({'unread_count': count})

@login_required
@require_POST
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
