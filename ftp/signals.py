from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    """Create a UserProfile automatically when a User is created."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved."""
    instance.profile.save()