from django.db import models
from django.conf import settings
from django.utils import timezone


# Create your models here.
class UnsubscribedUser(models.Model):
    email = models.EmailField(unique=True)
    unsubscribed_from = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='unsubscribed_users')
    unsubscribed_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.email