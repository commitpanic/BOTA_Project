from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, UserStatistics


@receiver(post_save, sender=User)
def create_user_statistics(sender, instance, created, **kwargs):
    """
    Automatically create UserStatistics for each new User.
    """
    if created:
        UserStatistics.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_statistics(sender, instance, **kwargs):
    """
    Ensure UserStatistics is saved when User is saved.
    """
    if hasattr(instance, 'statistics'):
        instance.statistics.save()
