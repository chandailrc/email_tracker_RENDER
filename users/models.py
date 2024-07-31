from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('free', 'Free User'),
        ('paid', 'Paid User'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='free')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username