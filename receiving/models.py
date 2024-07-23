# receiving/models.py

from django.db import models
from django.utils import timezone
from sending.models import Email

class ReceivedEmail(models.Model):
    sender = models.EmailField()
    recipients = models.JSONField()  # Store as a list of email addresses
    cc = models.JSONField(null=True, blank=True)  # Store as a list of email addresses
    bcc = models.JSONField(null=True, blank=True)  # Store as a list of email addresses
    subject = models.CharField(max_length=255)
    body = models.TextField()
    received_at = models.DateTimeField(default=timezone.now)
    in_reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    original_sent_email = models.ForeignKey(Email, null=True, blank=True, on_delete=models.SET_NULL, related_name='received_replies')
    message_id = models.CharField(max_length=255, unique=True)
    headers = models.JSONField()  # Store full email headers
    html_body = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Email from {self.sender}: {self.subject}"

class Attachment(models.Model):
    email = models.ForeignKey(ReceivedEmail, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.IntegerField()

    def __str__(self):
        return f"Attachment: {self.filename} for {self.email}"