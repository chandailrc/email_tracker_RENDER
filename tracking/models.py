from django.db import models
from django.utils import timezone
from sending.models import SentEmail, Link


class TrackingLog(models.Model):
    email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
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
    
class EmailInteraction(models.Model):
    email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=50)  # 'open', 'click', 'form_submission'
    timestamp = models.DateTimeField(auto_now_add=True)
    related_open = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.email} - {self.interaction_type} at {self.timestamp}"

class GenuineOpen(models.Model):
    email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    open_event = models.ForeignKey(EmailInteraction, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        unique_together = ('email', 'open_event')
    