from django.utils import timezone
from cluster.models import Cluster


def active_activations(request):
    """Context processor to show LIVE badge when there are active spots"""
    today = timezone.now().date()
    
    # Check if there are any active spots (clusters) from today
    # This shows real ON AIR activity
    active_spots_count = Cluster.objects.filter(
        timestamp__date=today
    ).count()
    
    return {
        'has_active_activations': active_spots_count > 0,
        'active_spots_count': active_spots_count,
    }