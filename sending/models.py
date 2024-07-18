from django.db import models
from django.utils import timezone


# Create your models here.
class Email(models.Model):
    recipient = models.EmailField()
    sender = models.EmailField(default='noreply@example.com')  # Default sender email
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Email to {self.recipient} from {self.sender}: {self.subject}"
    
class TrackingPixelToken(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    token = models.CharField(max_length=32, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        return self.expires_at <= timezone.now()

class Link(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    url = models.URLField()