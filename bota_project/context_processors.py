from django.utils import timezone
from cluster.models import Spot


def active_activations(request):
    """Context processor to show LIVE badge when there are active spots"""
    # Check if there are any active spots (not expired)
    # This shows real ON AIR activity
    active_spots_count = Spot.objects.filter(
        is_active=True,
        expires_at__gt=timezone.now()
    ).count()
    
    return {
        'has_active_activations': active_spots_count > 0,
        'active_spots_count': active_spots_count,
    }