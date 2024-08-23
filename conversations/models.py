from django.db import models
from django.utils import timezone
from sending.models import SentEmail
from receiving.models import ReceivedEmail
from django.conf import settings


class Conversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    last_updated = models.DateTimeField(auto_now=True)
    is_new = models.BooleanField(default=True)
    unread = models.BooleanField(default=True)
    unread_count = models.IntegerField(default=0)

    def mark_as_read(self):
        self.is_new = False
        self.unread = False
        self.unread_count = 0
        self.save(update_fields=['is_new', 'unread', 'unread_count'])

    def increment_unread_count(self):
        if not self.is_new:
            self.unread_count += 1
            self.unread = True
            self.save(update_fields=['unread_count', 'unread'])
    
    def reset_unread_count(self):
        self.unread_count = 0
        self.unread = False
        self.save(update_fields=['unread_count', 'unread'])
    
    def save(self, *args, **kwargs):
        delivered_timestamp = kwargs.pop('delivered_timestamp', None)
        if delivered_timestamp:
            self.last_updated = delivered_timestamp
        elif not self.id:
            self.last_updated = timezone.now()
        super(Conversation, self).save(*args, **kwargs)
        
    # if delivered_timestamp==None
    # If the instance is new (not self.id is True):
    #     last_updated is set to the current time (timezone.now()).

    # If the instance is not new (already saved before):  
    #     last_updated is not explicitly set within the modified save method and instead will be updated by auto_now=True, which also sets it to the current time.
    
    def __str__(self):
        return f"{self.subject} (Last updated: {self.last_updated})"
    


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    email = models.EmailField()
    
    class Meta:
        unique_together = ['conversation', 'email']
    
    def __str__(self):
        return f"{self.email} in {self.conversation}"

class ConversationMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    sent_email = models.OneToOneField(SentEmail, on_delete=models.SET_NULL, null=True, blank=True)
    received_email = models.OneToOneField(ReceivedEmail, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    content = models.TextField()  # Add this field

    def __str__(self):
        return f"Message in {self.conversation} at {self.timestamp}"
    
    @property
    def sender(self):
        return self.sent_email.sender if self.sent_email else self.received_email.sender
    
    @property
    def email_id(self):
        return self.sent_email.id if self.sent_email else self.received_email.id
    
    @property
    def sendOrRec(self):
        return 'send' if self.sent_email else 'received'