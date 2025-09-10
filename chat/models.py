from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class Conversation(models.Model):
    """Conversația dintre doi utilizatori despre un anunț"""
    participants = models.ManyToManyField(User, related_name='conversations', verbose_name="Participanți")
    listing = models.ForeignKey('listings.Listing', on_delete=models.CASCADE, related_name='conversations', verbose_name="Anunț")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Creat la")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Actualizat la")
    is_active = models.BooleanField(default=True, verbose_name="Activ")
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = "Conversație"
        verbose_name_plural = "Conversații"
    
    def __str__(self):
        participants_names = " & ".join([p.username for p in self.participants.all()])
        return f"Conversație: {participants_names} - {self.listing.title}"
    
    def get_absolute_url(self):
        return reverse('chat:conversation', kwargs={'pk': self.pk})
    
    def get_other_participant(self, current_user):
        """Returnează celălalt participant din conversație"""
        return self.participants.exclude(id=current_user.id).first()
    
    def get_last_message(self):
        """Returnează ultimul mesaj din conversație"""
        return self.messages.first()
    
    def mark_as_read(self, user):
        """Marchează toate mesajele ca citite pentru un utilizator"""
        self.messages.filter(receiver=user, is_read=False).update(is_read=True)


class Message(models.Model):
    """Mesaj într-o conversație"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name="Conversație")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="Expeditor")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', verbose_name="Destinatar")
    content = models.TextField(verbose_name="Conținut")
    is_read = models.BooleanField(default=False, verbose_name="Citit")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Trimis la")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mesaj"
        verbose_name_plural = "Mesaje"
    
    def __str__(self):
        return f"De la {self.sender.username} către {self.receiver.username}: {self.content[:50]}..."
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizează timpul conversației
        self.conversation.save()


class MessageAttachment(models.Model):
    """Atașamente pentru mesaje (imagini, documente)"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments', verbose_name="Mesaj")
    file = models.FileField(upload_to='chat/attachments/', verbose_name="Fișier")
    filename = models.CharField(max_length=255, verbose_name="Nume fișier")
    file_type = models.CharField(max_length=50, verbose_name="Tip fișier")
    file_size = models.IntegerField(verbose_name="Dimensiune fișier")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Atașament mesaj"
        verbose_name_plural = "Atașamente mesaje"
    
    def __str__(self):
        return f"Atașament: {self.filename}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.filename = self.file.name
            self.file_size = self.file.size
            # Determină tipul fișierului
            if self.file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                self.file_type = 'image'
            elif self.file.name.lower().endswith(('.pdf', '.doc', '.docx', '.txt')):
                self.file_type = 'document'
            else:
                self.file_type = 'other'
        super().save(*args, **kwargs)
