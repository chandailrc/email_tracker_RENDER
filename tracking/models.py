from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
import json

class Email(models.Model):
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)

class TrackingLog(models.Model):
    email = models.ForeignKey(Email, on_delete=models.CASCADE)
    opened_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    is_expired_open = models.BooleanField(default=False)
    tracking_type = models.CharField(max_length=255, default='default')
    #tracking_type = models.CharField(max_length=10, choices=[('pixel', 'Pixel'), ('css', 'CSS')])

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
    

class UnsubscribedUser(models.Model):
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.email
