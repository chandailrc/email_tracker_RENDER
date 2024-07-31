from django.db import models
from django.utils import timezone
from django.conf import settings

class SentEmail(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_emails')
    recipient = models.EmailField()
    cc = models.TextField(blank=True, help_text="Comma-separated list of CC email addresses")
    bcc = models.TextField(blank=True, help_text="Comma-separated list of BCC email addresses")
    sender = models.EmailField()  # We'll set this dynamically based on the user's email
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    message_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    thread_id = models.CharField(max_length=255, null=True, blank=True)
    in_reply_to = models.ForeignKey('receiving.ReceivedEmail', null=True, blank=True, on_delete=models.SET_NULL, related_name='sent_replies')

    def __str__(self):
        return f"Email to {self.recipient} from {self.sender}: {self.subject}"

    def get_cc_list(self):
        return [email.strip() for email in self.cc.split(',') if email.strip()]

    def get_bcc_list(self):
        return [email.strip() for email in self.bcc.split(',') if email.strip()]

class TrackingPixelToken(models.Model):
    email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    token = models.CharField(max_length=32, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.expires_at > timezone.now()

class Link(models.Model):
    email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    url = models.URLField()