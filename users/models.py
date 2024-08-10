from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth import get_user_model
User = get_user_model() 
# COULD have used settings.AUTH_USER_MODEL), both can be used interchangeably. Usually used together to prevent circular imports
# Remember get_user_model is a function that returns the model, whereas settings.AUTH_USER_MODEL is a string

class UserProfile(models.Model):
    USER_TYPE_CHOICES = (
        ('free', 'Free User'),
        ('paid', 'Paid User'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='free')
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()