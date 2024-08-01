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
    
    def __str__(self):
        return f"Message in {self.conversation} at {self.timestamp}"
    
    @property
    def sender(self):
        return self.sent_email.sender if self.sent_email else self.received_email.sender
    
    @property
    def content(self):
        return self.sent_email.body if self.sent_email else self.received_email.body