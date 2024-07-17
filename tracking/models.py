from django.db import models
from django.utils import timezone


class Email(models.Model):
    recipient = models.EmailField()
    sender = models.EmailField(default='noreply@example.com')  # Default sender email
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Email to {self.recipient} from {self.sender}: {self.subject}"


class TrackingLog(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    opened_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    is_expired_open = models.BooleanField(default=False)
    tracking_type = models.CharField(max_length=255, default='default')
    geo_location = models.CharField(max_length=255, null=True, blank=True)
    referer = models.URLField(null=True, blank=True)
    device_type = models.CharField(max_length=255, null=True, blank=True)
    screen_resolution = models.CharField(max_length=255, null=True, blank=True)
    language = models.CharField(max_length=255, null=True, blank=True)
    protocol = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=255, null=True, blank=True)
    host = models.CharField(max_length=255, null=True, blank=True)
    connection = models.CharField(max_length=255, null=True, blank=True)

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

class LinkClick(models.Model):
    link = models.ForeignKey(Link, on_delete=models.CASCADE)
    clicked_at = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    geo_location = models.CharField(max_length=255, null=True, blank=True)
    referer = models.URLField(null=True, blank=True)
    device_type = models.CharField(max_length=255, null=True, blank=True)
    screen_resolution = models.CharField(max_length=255, null=True, blank=True)
    language = models.CharField(max_length=255, null=True, blank=True)
    protocol = models.CharField(max_length=255, null=True, blank=True)
    method = models.CharField(max_length=255, null=True, blank=True)
    host = models.CharField(max_length=255, null=True, blank=True)
    connection = models.CharField(max_length=255, null=True, blank=True)

class UnsubscribedUser(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email

