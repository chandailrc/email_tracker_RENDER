from django.db import models
from django.utils import timezone
import uuid
from sending.models import SentEmail

class TrackingItem(models.Model):
    TYPES = (
        ('PIXEL', 'Pixel'),
        ('LINK', 'Link'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    item_type = models.CharField(max_length=5, choices=TYPES)
    url = models.URLField(null=True, blank=True)  # Only for links
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        return self.expires_at > timezone.now()
    
class TrackingEvent(models.Model):
    tracking_item = models.ForeignKey(TrackingItem, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
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
    INTERACTION_TYPES = (
        ('OPEN', 'Open'),
        ('CLICK', 'Click'),
    )
    email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.email} - {self.interaction_type} at {self.timestamp}"

class GenuineOpen(models.Model):
    email = models.ForeignKey(SentEmail, on_delete=models.CASCADE)
    open_event = models.ForeignKey(EmailInteraction, on_delete=models.CASCADE, null=True, blank=True)    
    class Meta:
        unique_together = ('email', 'open_event')