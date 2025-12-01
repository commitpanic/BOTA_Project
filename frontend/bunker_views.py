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
import csv
import io

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
    
    # For logged-in users, get activated and hunted bunkers
    activated_bunker_ids = set()
    hunted_bunker_ids = set()
    
    if request.user.is_authenticated:
        from activations.models import ActivationLog
        
        # Get bunkers activated by user
        activated_bunker_ids = set(
            ActivationLog.objects.filter(
                activator=request.user
            ).values_list('bunker_id', flat=True).distinct()
        )
        
        # Get bunkers hunted by user (as hunter, not activator)
        hunted_bunker_ids = set(
            ActivationLog.objects.filter(
                user=request.user
            ).exclude(activator=request.user).values_list('bunker_id', flat=True).distinct()
        )
    
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
        'activated_bunker_ids': activated_bunker_ids,
        'hunted_bunker_ids': hunted_bunker_ids,
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
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                bunker_type=request.POST.get('bunker_type', ''),
                latitude=Decimal(request.POST.get('latitude')),
                longitude=Decimal(request.POST.get('longitude')),
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
        default_category, created = BunkerCategory.objects.get_or_create(
            name_en='WW2 Bunker',
            defaults={
                'name_pl': 'Bunkier z II WŚ',
                'description_en': 'World War 2 fortification',
                'description_pl': 'Fortyfikacja z czasów II Wojny Światowej',
            }
        )
        
        # Generate next reference number
        # Find the last bunker with B/SP- prefix
        last_bunker = Bunker.objects.filter(
            reference_number__startswith='B/SP-'
        ).order_by('-reference_number').first()
        
        if last_bunker:
            # Extract number from reference like "B/SP-0258"
            try:
                last_number = int(last_bunker.reference_number.split('-')[1])
                next_number = last_number + 1
            except (IndexError, ValueError):
                # If parsing fails, start from 1
                next_number = 1
        else:
            # No bunkers yet, start from 1
            next_number = 1
        
        # Format as B/SP-XXXX (4 digits with leading zeros)
        reference_number = f"B/SP-{next_number:04d}"
        
        # Create the bunker
        bunker = Bunker.objects.create(
            reference_number=reference_number,
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
            _('Bunker request approved and %(ref)s created.') % {'ref': bunker.reference_number}
        )
        
    except Exception as e:
        messages.error(request, _('Error approving request: %(error)s') % {'error': str(e)})
    
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


@staff_member_required
def upload_bunkers_csv(request):
    """
    Upload bunkers from CSV file (Admin only)
    
    Expected CSV format:
    reference_number,name_en,name_pl,description_en,description_pl,category,latitude,longitude,locator
    """
    if request.method == 'POST' and request.FILES.get('file'):
        try:
            csv_file = request.FILES['file']
            
            # Check file extension
            if not csv_file.name.endswith('.csv'):
                messages.error(request, _('File must be a CSV file (.csv)'))
                return redirect('upload_bunkers_csv')
            
            # Read and decode the file
            file_data = csv_file.read().decode('utf-8')
            io_string = io.StringIO(file_data)
            reader = csv.DictReader(io_string)
            
            created_count = 0
            updated_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                try:
                    # Support multiple column name variations for reference
                    reference = (row.get('reference_number') or 
                                row.get('Reference') or 
                                row.get('reference') or 
                                row.get('ref') or '').strip()
                    if not reference:
                        errors.append(f"Row {row_num}: Missing reference_number (or Reference)")
                        error_count += 1
                        continue
                    
                    # Get or create category - support multiple column names
                    category_name = (row.get('category') or 
                                    row.get('Category') or 
                                    row.get('Type') or 
                                    row.get('type') or 
                                    'Military').strip()
                    category, cat_created = BunkerCategory.objects.get_or_create(
                        name_en=category_name,
                        defaults={
                            'name_pl': category_name,
                            'description_en': f'{category_name} bunkers',
                            'description_pl': f'Bunkry typu {category_name}',
                        }
                    )
                    
                    # Parse coordinates - support multiple column names
                    try:
                        lat_value = (row.get('latitude') or row.get('Lat') or 
                                    row.get('lat') or '0').strip()
                        lon_value = (row.get('longitude') or row.get('Long') or 
                                    row.get('lon') or row.get('lng') or '0').strip()
                        latitude = Decimal(lat_value)
                        longitude = Decimal(lon_value)
                    except:
                        errors.append(f"Row {row_num}: Invalid coordinates for {reference}")
                        error_count += 1
                        continue
                    
                    # Handle flexible naming - support Name, name, name_en, name_pl
                    name_value = (row.get('Name') or row.get('name') or 
                                 row.get('name_en') or row.get('name_pl') or 
                                 reference).strip()
                    
                    if row.get('name_en') or row.get('name_pl'):
                        name_en = row.get('name_en', name_value).strip()
                        name_pl = row.get('name_pl', name_value).strip()
                    else:
                        name_en = name_value
                        name_pl = name_value
                    
                    # Handle flexible description - support Type, description, description_en, description_pl
                    desc_value = (row.get('description') or row.get('Description') or 
                                 row.get('Type') or row.get('type') or '').strip()
                    
                    if row.get('description_en') or row.get('description_pl'):
                        desc_en = row.get('description_en', desc_value).strip()
                        desc_pl = row.get('description_pl', desc_value).strip()
                    else:
                        desc_en = desc_value
                        desc_pl = desc_value
                    
                    # Get locator - support multiple column names
                    locator_value = (row.get('locator') or row.get('Locator') or 
                                    row.get('grid') or row.get('Grid') or '').strip()
                    
                    # Create or update bunker
                    bunker, created = Bunker.objects.update_or_create(
                        reference_number=reference,
                        defaults={
                            'name_en': name_en,
                            'name_pl': name_pl,
                            'description_en': desc_en,
                            'description_pl': desc_pl,
                            'category': category,
                            'latitude': latitude,
                            'longitude': longitude,
                            'locator': locator_value,
                            'is_verified': True,
                            'verified_by': request.user,
                            'created_by': request.user,
                        }
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                        
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
            
            # Show results
            if created_count > 0:
                messages.success(request, _(f'Successfully created {created_count} bunker(s).'))
            if updated_count > 0:
                messages.info(request, _(f'Updated {updated_count} existing bunker(s).'))
            if error_count > 0:
                messages.warning(request, _(f'Failed to process {error_count} row(s).'))
                for error in errors[:5]:  # Show first 5 errors
                    messages.error(request, error)
                if len(errors) > 5:
                    messages.error(request, _(f'...and {len(errors) - 5} more errors.'))
            
            return redirect('bunker_list')
            
        except Exception as e:
            messages.error(request, _(f'Error processing CSV file: {str(e)}'))
    
    return render(request, 'upload_bunkers_csv.html')
