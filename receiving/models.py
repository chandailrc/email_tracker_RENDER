from django.db import models
from django.utils import timezone

class ReceivedEmail(models.Model):
    sender = models.EmailField()
    recipient = models.EmailField()
    cc = models.TextField(blank=True, help_text="Comma-separated list of CC email addresses")
    bcc = models.TextField(blank=True, help_text="Comma-separated list of BCC email addresses")
    subject = models.CharField(max_length=255)
    body = models.TextField()
    received_at = models.DateTimeField(default=timezone.now)
    in_reply_to = models.ForeignKey('sending.SentEmail', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    message_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    thread_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Email from {self.sender} to {self.recipient}: {self.subject}"

    def get_cc_list(self):
        return [email.strip() for email in self.cc.split(',') if email.strip()]

    def get_bcc_list(self):
        return [email.strip() for email in self.bcc.split(',') if email.strip()]

class Attachment(models.Model):
    email = models.ForeignKey(ReceivedEmail, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='email_attachments/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)

    def __str__(self):
        return f"Attachment: {self.filename} for {self.email}"