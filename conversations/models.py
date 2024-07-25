from django.db import models
from sending.models import Email as SentEmail
from receiving.models import ReceivedEmail

class Conversation(models.Model):
    subject = models.CharField(max_length=255)
    last_updated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.subject

class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='participants')
    email = models.EmailField()

    def __str__(self):
        return f"{self.email} in {self.conversation}"

class ConversationMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sent_email = models.ForeignKey(SentEmail, on_delete=models.SET_NULL, null=True, blank=True)
    received_email = models.ForeignKey(ReceivedEmail, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message in {self.conversation} at {self.timestamp}"