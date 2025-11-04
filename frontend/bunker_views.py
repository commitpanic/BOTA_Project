"""
Bunker management views with filtering and search
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils.translation import gettext as _
from decimal import Decimal

from bunkers.models import Bunker, BunkerCategory, BunkerRequest


def bunker_list(request):
    """
    Public bunker list with comprehensive filtering and search
    """
    bunkers = Bunker.objects.select_related('category', 'verified_by').all()
    
    # Search query
    search = request.GET.get('search', '').strip()
    if search:
        bunkers = bunkers.filter(
            Q(reference_number__icontains=search) |
            Q(name_en__icontains=search) |
            Q(name_pl__icontains=search) |
            Q(description_en__icontains=search) |
            Q(description_pl__icontains=search)
        )
    
    # Filter by verification status
    status = request.GET.get('status', '')
    if status == 'verified':
        bunkers = bunkers.filter(is_verified=True)
    elif status == 'pending':
        bunkers = bunkers.filter(is_verified=False)
    
    # Filter by category
    category_id = request.GET.get('category', '')
    if category_id:
        bunkers = bunkers.filter(category_id=category_id)
    
    # Filter by reference prefix (e.g., B/SP-)
    prefix = request.GET.get('prefix', '').strip()
    if prefix:
        bunkers = bunkers.filter(reference_number__istartswith=prefix)
    
    # Sorting
    sort = request.GET.get('sort', 'reference')
    if sort == 'name':
        bunkers = bunkers.order_by('name_en')
    elif sort == 'date':
        bunkers = bunkers.order_by('-created_at')
    else:  # default: reference
        bunkers = bunkers.order_by('reference_number')
    
    # Get categories for filter dropdown
    categories = BunkerCategory.objects.all()
    
    # Count statistics
    total_bunkers = Bunker.objects.count()
    verified_count = Bunker.objects.filter(is_verified=True).count()
    pending_count = Bunker.objects.filter(is_verified=False).count()
    
    context = {
        'bunkers': bunkers,
        'categories': categories,
        'search': search,
        'status': status,
        'category_id': category_id,
        'prefix': prefix,
        'sort': sort,
        'total_bunkers': total_bunkers,
        'verified_count': verified_count,
        'pending_count': pending_count,
    }
    return render(request, 'bunkers/list.html', context)


@login_required
def request_bunker(request):
    """
    User request form to add a new bunker (requires approval)
    """
    if request.method == 'POST':
        try:
            bunker_request = BunkerRequest.objects.create(
                reference_number=request.POST.get('reference_number'),
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                bunker_type=request.POST.get('bunker_type', ''),
                latitude=Decimal(request.POST.get('latitude')),
                longitude=Decimal(request.POST.get('longitude')),
                locator=request.POST.get('locator', ''),
                photo_url=request.POST.get('photo_url', ''),
                additional_info=request.POST.get('additional_info', ''),
                requested_by=request.user,
                status='pending'
            )
            
            messages.success(
                request,
                _('Your bunker request has been submitted and is pending review.')
            )
            return redirect('my_bunker_requests')
            
        except Exception as e:
            messages.error(request, _(f'Error submitting request: {str(e)}'))
    
    return render(request, 'bunkers/request.html')


@login_required
def my_bunker_requests(request):
    """
    View user's own bunker requests
    """
    requests_list = BunkerRequest.objects.filter(
        requested_by=request.user
    ).select_related('bunker', 'reviewed_by').order_by('-created_at')
    
    context = {
        'requests': requests_list,
    }
    return render(request, 'bunkers/my_requests.html', context)


@staff_member_required
def manage_bunker_requests(request):
    """
    Staff/Admin view to approve or reject bunker requests
    """
    status_filter = request.GET.get('status', 'pending')
    
    requests_list = BunkerRequest.objects.select_related(
        'requested_by', 'reviewed_by', 'bunker'
    )
    
    if status_filter:
        requests_list = requests_list.filter(status=status_filter)
    
    requests_list = requests_list.order_by('-created_at')
    
    context = {
        'requests': requests_list,
        'status_filter': status_filter,
    }
    return render(request, 'bunkers/manage_requests.html', context)


@staff_member_required
def approve_bunker_request(request, request_id):
    """
    Approve a bunker request and create the bunker
    """
    bunker_request = get_object_or_404(BunkerRequest, id=request_id)
    
    if bunker_request.status != 'pending':
        messages.warning(request, _('This request has already been processed.'))
        return redirect('manage_bunker_requests')
    
    try:
        # Get or create default category
        default_category, _ = BunkerCategory.objects.get_or_create(
            name_en='WW2 Bunker',
            defaults={
                'name_pl': 'Bunkier z II WŚ',
                'description_en': 'World War 2 fortification',
                'description_pl': 'Fortyfikacja z czasów II Wojny Światowej',
            }
        )
        
        # Create the bunker
        bunker = Bunker.objects.create(
            reference_number=bunker_request.reference_number,
            name_en=bunker_request.name,
            name_pl=bunker_request.name,
            description_en=f"{bunker_request.bunker_type}. {bunker_request.description}",
            description_pl=f"{bunker_request.bunker_type}. {bunker_request.description}",
            category=default_category,
            latitude=bunker_request.latitude,
            longitude=bunker_request.longitude,
            is_verified=True,
            verified_by=request.user,
            created_by=bunker_request.requested_by
        )
        
        # Update request status
        bunker_request.status = 'approved'
        bunker_request.reviewed_by = request.user
        bunker_request.bunker = bunker
        bunker_request.save()
        
        messages.success(
            request,
            _(f'Bunker request approved and {bunker.reference_number} created.')
        )
        
    except Exception as e:
        messages.error(request, _(f'Error approving request: {str(e)}'))
    
    return redirect('manage_bunker_requests')


@staff_member_required
def reject_bunker_request(request, request_id):
    """
    Reject a bunker request with reason
    """
    bunker_request = get_object_or_404(BunkerRequest, id=request_id)
    
    if bunker_request.status != 'pending':
        messages.warning(request, _('This request has already been processed.'))
        return redirect('manage_bunker_requests')
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        bunker_request.status = 'rejected'
        bunker_request.rejection_reason = reason
        bunker_request.reviewed_by = request.user
        bunker_request.save()
        
        messages.success(request, _('Bunker request rejected.'))
        return redirect('manage_bunker_requests')
    
    context = {
        'bunker_request': bunker_request,
    }
    return render(request, 'bunkers/reject.html', context)


def bunker_detail(request, reference):
    """
    Detailed view of a single bunker
    """
    bunker = get_object_or_404(
        Bunker.objects.select_related('category', 'verified_by', 'created_by'),
        reference_number=reference
    )
    
    # Get activation statistics for this bunker
    from activations.models import ActivationLog
    activation_count = ActivationLog.objects.filter(bunker=bunker).count()
    unique_activators = ActivationLog.objects.filter(bunker=bunker).values('activator').distinct().count()
    
    context = {
        'bunker': bunker,
        'activation_count': activation_count,
        'unique_activators': unique_activators,
    }
    return render(request, 'bunkers/detail.html', context)
