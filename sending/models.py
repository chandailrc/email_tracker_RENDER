from django.db import models
from django.utils import timezone
from django.conf import settings

class SentEmail(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_emails')
    recipient = models.EmailField()
    sender = models.EmailField()  # We'll set this dynamically based on the user's email
    cc = models.TextField(blank=True, help_text="Comma-separated list of CC email addresses")
    bcc = models.TextField(blank=True, help_text="Comma-separated list of BCC email addresses")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    in_reply_to = models.CharField(max_length=255, unique=True, null=True, blank=True)
    message_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    thread_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Email to {self.recipient} from {self.sender}: {self.subject}"

    def get_cc_list(self):
        return [email.strip() for email in self.cc.split(',') if email.strip()]

    def get_bcc_list(self):
        return [email.strip() for email in self.bcc.split(',') if email.strip()]
