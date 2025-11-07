from django.utils import timezone
from planned_activations.models import PlannedActivation


def active_activations(request):
    """Context processor to provide active activations globally"""
    today = timezone.now().date()
    
    # Check if there are any activations planned for today
    active_count = PlannedActivation.objects.filter(
        planned_date=today
    ).count()
    
    return {
        'has_active_activations': active_count > 0,
        'active_activations_count': active_count,
    }