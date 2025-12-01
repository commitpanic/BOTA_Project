"""
Frontend views for BOTA Project
Handles user-facing pages with i18n support
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Count, Sum, Max
from django.utils.translation import gettext as _
from django.core.cache import cache
from accounts.models import User, UserStatistics
from bunkers.models import Bunker
from activations.models import ActivationLog
from diplomas.models import Diploma, DiplomaProgress


def home(request):
    """Home page with program statistics"""
    
    # Try to get cached statistics
    cache_key = 'home_statistics'
    context = cache.get(cache_key)
    
    if context is None:
        # Cache miss - calculate statistics
        # Get recent activations grouped by activator, bunker, and date
        # Show activators with their QSO count for each activation
        
        recent_activations = ActivationLog.objects.values(
            'activator__callsign',
            'bunker__reference_number',
            'bunker__name_en'
        ).annotate(
            qso_count=Count('id'),
            latest_qso=Max('activation_date')
        ).order_by('-latest_qso')[:10]
        
        context = {
            'total_bunkers': Bunker.objects.filter(is_verified=True).count(),
            'total_users': User.objects.filter(is_active=True).count(),
            'total_qsos': ActivationLog.objects.count(),
            'total_diplomas': Diploma.objects.count(),
            'recent_activations': list(recent_activations),  # Convert to list for caching
        }
        
        # Cache for 15 minutes (900 seconds)
        cache.set(cache_key, context, 900)
    
    return render(request, 'home.html', context)


@login_required
def dashboard(request):
    """User dashboard with statistics and progress"""
    from diplomas.models import DiplomaType
    from django.db.models.functions import TruncDate
    
    # Get or create user statistics
    stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    # Get earned diplomas
    earned_diplomas = Diploma.objects.filter(
        user=request.user
    ).select_related('diploma_type').order_by('-issue_date')
    
    # Get IDs of earned diploma types
    earned_diploma_type_ids = earned_diplomas.values_list('diploma_type_id', flat=True)
    
    # Get all active diploma types not yet earned
    available_diploma_types = DiplomaType.objects.filter(
        is_active=True
    ).exclude(
        id__in=earned_diploma_type_ids
    ).order_by('category', 'display_order')
    
    # Calculate current user stats for progress
    unique_activations = ActivationLog.objects.filter(
        activator=request.user
    ).values('bunker').distinct().count()
    
    total_activations = ActivationLog.objects.filter(
        activator=request.user
    ).annotate(
        activation_day=TruncDate('activation_date')
    ).values('bunker', 'activation_day').distinct().count()
    
    unique_hunted = ActivationLog.objects.filter(
        user=request.user
    ).exclude(activator=request.user).values('bunker').distinct().count()
    
    total_hunted = unique_hunted
    
    # For each available diploma type, get or create progress
    all_progress = []
    for diploma_type in available_diploma_types:
        progress, created = DiplomaProgress.objects.get_or_create(
            user=request.user,
            diploma_type=diploma_type
        )
        
        # Activator points = activation sessions (not QSOs)
        progress.update_points(
            activator=total_activations,
            hunter=stats.hunter_points,
            b2b=stats.b2b_points,
            unique_activations=unique_activations,
            total_activations=total_activations,
            unique_hunted=unique_hunted,
            total_hunted=total_hunted
        )
        
        all_progress.append(progress)
    
    # Organize progress by category - show top 2 from each category
    activator_progress = sorted([p for p in all_progress if p.diploma_type.category == 'activator'], 
                                 key=lambda p: p.diploma_type.display_order)[:2]
    hunter_progress = sorted([p for p in all_progress if p.diploma_type.category == 'hunter'], 
                             key=lambda p: p.diploma_type.display_order)[:2]
    b2b_progress = sorted([p for p in all_progress if p.diploma_type.category == 'b2b'], 
                          key=lambda p: p.diploma_type.display_order)[:2]
    special_progress = sorted([p for p in all_progress if p.diploma_type.category in ['special_event', 'cluster', 'other']], 
                              key=lambda p: p.diploma_type.display_order)[:2]
    
    # Get recent activity - both as activator and hunter
    from django.db.models import Q
    recent_logs = ActivationLog.objects.filter(
        Q(user=request.user) | Q(activator=request.user)
    ).select_related('bunker', 'activator', 'user').order_by('-activation_date').distinct()[:10]
    
    context = {
        'stats': stats,
        'activator_progress': activator_progress,
        'hunter_progress': hunter_progress,
        'b2b_progress': b2b_progress,
        'special_progress': special_progress,
        'recent_logs': recent_logs,
    }
    return render(request, 'dashboard.html', context)


@login_required
def upload_log(request):
    """ADIF log upload page"""
    if request.method == 'POST':
        from activations.log_import_service import LogImportService
        
        if 'file' not in request.FILES:
            messages.error(request, _('No file uploaded'))
            return redirect('upload_log')
        
        file = request.FILES['file']
        
        # Validate file extension
        if not file.name.endswith('.adi'):
            messages.error(request, _('File must have .adi extension'))
            return redirect('upload_log')
        
        try:
            # Read file content
            content = file.read().decode('utf-8')
            
            # Process upload
            service = LogImportService()
            result = service.process_adif_upload(content, request.user, filename=file.name)
            
            # Check if successful
            if not result.get('success'):
                errors = result.get('errors', ['Unknown error'])
                for error in errors:
                    messages.error(request, error)
                return redirect('upload_log')
            
            # Show success message with statistics
            success_msg = _(f'Successfully processed {result["qsos_processed"]} new QSOs from {result["bunker"]}.')
            if result.get('qsos_duplicates', 0) > 0:
                success_msg += _(f' Skipped {result["qsos_duplicates"]} duplicates.')
            if result.get('b2b_qsos', 0) > 0:
                success_msg += _(f' B2B QSOs: {result["b2b_qsos"]}.')
            
            messages.success(request, success_msg)
            
            # Show warnings if any (but not for duplicates)
            for warning in result.get('warnings', []):
                messages.warning(request, warning)
            
            # Redirect to log history with highlight of new upload
            log_upload_id = result.get('log_upload_id')
            return redirect(f"{reverse('log_history')}#upload-{log_upload_id}")
            
        except Exception as e:
            messages.error(request, _(f'Error processing file: {str(e)}'))
            return redirect('upload_log')
    
    return render(request, 'upload_log.html')


@login_required
def diplomas_view(request):
    """User diplomas and progress"""
    from diplomas.models import DiplomaType
    from activations.models import ActivationLog
    from django.db.models import Q, Count
    
    # Get earned diplomas
    earned_diplomas = Diploma.objects.filter(
        user=request.user
    ).select_related('diploma_type').order_by('-issue_date')
    
    # Get IDs of earned diploma types
    earned_diploma_type_ids = earned_diplomas.values_list('diploma_type_id', flat=True)
    
    # Get or create user statistics
    stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    # Get all active diploma types not yet earned
    available_diploma_types = DiplomaType.objects.filter(
        is_active=True
    ).exclude(
        id__in=earned_diploma_type_ids
    ).order_by('category', 'display_order')
    
    # Calculate current user stats for progress
    # Unique activations = distinct bunkers activated
    unique_activations = ActivationLog.objects.filter(
        activator=request.user
    ).values('bunker').distinct().count()
    
    # Total activations = distinct (bunker, date) combinations
    # Each activation session counts as one, regardless of QSO count
    from django.db.models.functions import TruncDate
    total_activations = ActivationLog.objects.filter(
        activator=request.user
    ).annotate(
        activation_day=TruncDate('activation_date')
    ).values('bunker', 'activation_day').distinct().count()
    
    # Unique hunted = distinct bunkers hunted (as non-activator)
    unique_hunted = ActivationLog.objects.filter(
        user=request.user
    ).exclude(activator=request.user).values('bunker').distinct().count()
    
    # Total hunted = count of distinct bunkers hunted (not QSOs)
    # For hunters, we count each unique bunker they worked
    total_hunted = unique_hunted
    
    # For each available diploma type, get or create progress with proper calculation
    all_progress = []
    for diploma_type in available_diploma_types:
        # Get or create progress record
        progress, created = DiplomaProgress.objects.get_or_create(
            user=request.user,
            diploma_type=diploma_type
        )
        
        # Update progress with current stats
        # Activator points = activation sessions (not QSOs)
        progress.update_points(
            activator=total_activations,
            hunter=stats.hunter_points,
            b2b=stats.b2b_points,
            unique_activations=unique_activations,
            total_activations=total_activations,
            unique_hunted=unique_hunted,
            total_hunted=total_hunted
        )
        
        all_progress.append(progress)
    
    # Organize progress by category
    activator_progress = [p for p in all_progress if p.diploma_type.category == 'activator']
    hunter_progress = [p for p in all_progress if p.diploma_type.category == 'hunter']
    b2b_progress = [p for p in all_progress if p.diploma_type.category == 'b2b']
    special_progress = [p for p in all_progress if p.diploma_type.category in ['special_event', 'cluster', 'other']]
    
    # Sort each category by display order
    activator_progress.sort(key=lambda p: p.diploma_type.display_order)
    hunter_progress.sort(key=lambda p: p.diploma_type.display_order)
    b2b_progress.sort(key=lambda p: p.diploma_type.display_order)
    special_progress.sort(key=lambda p: p.diploma_type.display_order)
    
    context = {
        'earned_diplomas': earned_diplomas,
        'activator_progress': activator_progress,
        'hunter_progress': hunter_progress,
        'b2b_progress': b2b_progress,
        'special_progress': special_progress,
    }
    return render(request, 'diplomas.html', context)


@login_required
def download_certificate(request, diploma_id):
    """Download diploma certificate as PDF using advanced customization"""
    from django.http import HttpResponse
    from django.utils.translation import get_language
    from diplomas.pdf_generator import generate_diploma_pdf
    
    # Get the diploma (ensure user owns it)
    diploma = get_object_or_404(Diploma, id=diploma_id, user=request.user)
    
    # Determine language
    current_lang = get_language()
    is_polish = current_lang == 'pl'
    
    # Prepare data
    callsign = diploma.user.callsign
    diploma_name = diploma.diploma_type.name_pl if is_polish else diploma.diploma_type.name_en
    date_text = f"{'Data wydania' if is_polish else 'Issue Date'}: {diploma.issue_date.strftime('%Y-%m-%d')}"
    
    # Points information
    points_parts = []
    if diploma.activator_points_earned > 0:
        points_parts.append(f"ACT: {diploma.activator_points_earned}")
    if diploma.hunter_points_earned > 0:
        points_parts.append(f"HNT: {diploma.hunter_points_earned}")
    if diploma.b2b_points_earned > 0:
        points_parts.append(f"B2B: {diploma.b2b_points_earned}")
    
    points_text = f"{'Punkty' if is_polish else 'Points'}: {' | '.join(points_parts)}" if points_parts else ""
    
    diploma_number = diploma.diploma_number
    verification_url = request.build_absolute_uri(f'/verify-diploma/{diploma.diploma_number}/')
    
    # Generate PDF
    buffer = generate_diploma_pdf(
        diploma_type=diploma.diploma_type,
        callsign=callsign,
        diploma_name=diploma_name,
        date_text=date_text,
        points_text=points_text,
        diploma_number=diploma_number,
        verification_url=verification_url,
        is_preview=False
    )
    
    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="BOTA_Diploma_{diploma.diploma_number}.pdf"'
    
    return response


def verify_diploma_view(request, diploma_number):
    """
    Public diploma verification page.
    Displays diploma details and authenticity confirmation.
    """
    from diplomas.models import DiplomaVerification
    
    # Try to find the diploma
    try:
        diploma = Diploma.objects.select_related(
            'user', 'diploma_type', 'issued_by'
        ).get(diploma_number=diploma_number)
        
        # Log the verification
        DiplomaVerification.objects.create(
            diploma=diploma,
            verified_by_ip=request.META.get('REMOTE_ADDR'),
            verified_by_user=request.user if request.user.is_authenticated else None,
            verification_method='qr'
        )
        
        # Get verification count
        verification_count = diploma.verifications.count()
        
        # Check if diploma type is still valid (for time-limited diplomas)
        is_valid = True
        if diploma.diploma_type.is_time_limited():
            is_valid = diploma.diploma_type.is_currently_valid()
        
        context = {
            'diploma': diploma,
            'verification_count': verification_count,
            'is_valid': is_valid,
            'verified': True,
        }
        
    except Diploma.DoesNotExist:
        context = {
            'verified': False,
            'diploma_number': diploma_number,
        }
    
    return render(request, 'verify_diploma.html', context)


@login_required
def profile_view(request):
    """User profile page with detailed statistics"""
    from activations.models import ActivationLog
    from bunkers.models import Bunker
    from django.db.models import Count, Q, Max
    
    stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    # Get activated bunkers (as activator) with bunker id for detail queries
    # Count distinct dates for actual activation count
    from django.db.models import Count, Max, Sum
    from django.db.models.functions import TruncDate
    
    activated_bunkers_raw = ActivationLog.objects.filter(
        activator=request.user
    ).annotate(
        activation_date_only=TruncDate('activation_date')
    ).values(
        'bunker__id',
        'bunker__reference_number', 
        'bunker__name_en', 
        'bunker__name_pl'
    ).annotate(
        activation_count=Count('activation_date_only', distinct=True),
        total_qso=Sum('qso_count'),
        last_activation=Max('activation_date')
    ).order_by('-activation_count')
    
    activated_bunkers = list(activated_bunkers_raw)
    
    # Get all activations for each bunker (for expandable details)
    # Group by date and aggregate modes and QSO counts
    all_activations = {}
    for bunker in activated_bunkers:
        bunker_id = bunker['bunker__id']
        from itertools import groupby
        
        # Get all activations for this bunker
        activations_query = ActivationLog.objects.filter(
            activator=request.user,
            bunker__id=bunker_id
        ).order_by('-activation_date')
        
        # Group by date (year-month-day) and aggregate
        grouped_activations = []
        for date_key, group_iter in groupby(activations_query, key=lambda x: x.activation_date.date()):
            group_list = list(group_iter)
            
            # Collect unique modes and bands
            modes = sorted(set(a.mode for a in group_list if a.mode))
            bands = sorted(set(a.band for a in group_list if a.band))
            
            # Sum QSO counts - properly handle None and 0 values
            total_qso = sum(a.qso_count if a.qso_count else 0 for a in group_list)
            
            # Check if any is B2B
            is_b2b = any(a.is_b2b for a in group_list)
            
            grouped_activations.append({
                'date': date_key,
                'bands': bands,
                'modes': modes,
                'total_qso': total_qso,
                'is_b2b': is_b2b,
                'count': len(group_list)
            })
        
        all_activations[bunker_id] = grouped_activations
    
    # Get hunted bunkers (as hunter/user)
    hunted_bunkers = ActivationLog.objects.filter(
        user=request.user
    ).exclude(activator=request.user).values(
        'bunker__id',
        'bunker__reference_number', 
        'bunker__name_en', 
        'bunker__name_pl'
    ).annotate(
        qso_count=Count('id'),
        last_qso=Max('activation_date')
    ).order_by('-qso_count')
    
    # Get all hunted QSOs for each bunker
    # Group by date and aggregate
    all_hunted_qsos = {}
    for bunker in hunted_bunkers:
        bunker_id = bunker['bunker__id']
        from django.db.models import Sum
        from itertools import groupby
        from operator import attrgetter
        
        # Get all hunted QSOs for this bunker
        qsos_query = ActivationLog.objects.filter(
            user=request.user,
            bunker__id=bunker_id
        ).exclude(activator=request.user).order_by('-activation_date')
        
        # Group by date (year-month-day) and aggregate
        grouped_qsos = []
        for date_key, group_iter in groupby(qsos_query, key=lambda x: x.activation_date.date()):
            group_list = list(group_iter)
            
            # Collect unique activators, modes and bands
            activators = sorted(set(a.activator.callsign for a in group_list if a.activator))
            modes = sorted(set(a.mode for a in group_list if a.mode))
            bands = sorted(set(a.band for a in group_list if a.band))
            
            # Count QSOs
            total_qso = len(group_list)
            
            # Check if any is B2B
            is_b2b = any(a.is_b2b for a in group_list)
            
            grouped_qsos.append({
                'date': date_key,
                'activators': activators,
                'bands': bands,
                'modes': modes,
                'total_qso': total_qso,
                'is_b2b': is_b2b
            })
        
        all_hunted_qsos[bunker_id] = grouped_qsos
    
    # Activator statistics by band
    activator_bands = ActivationLog.objects.filter(
        activator=request.user
    ).values('band').annotate(
        count=Count('id'),
        qso_sum=Count('qso_count')
    ).order_by('-count')
    
    # Activator statistics by mode
    activator_modes = ActivationLog.objects.filter(
        activator=request.user
    ).values('mode').annotate(
        count=Count('id'),
        qso_sum=Count('qso_count')
    ).order_by('-count')
    
    # Hunter statistics by band
    hunter_bands = ActivationLog.objects.filter(
        user=request.user
    ).exclude(activator=request.user).values('band').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Hunter statistics by mode
    hunter_modes = ActivationLog.objects.filter(
        user=request.user
    ).exclude(activator=request.user).values('mode').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Get non-activated bunkers (for activator)
    activated_bunker_ids = [b['bunker__id'] for b in activated_bunkers]
    non_activated_bunkers = Bunker.objects.exclude(
        id__in=activated_bunker_ids
    ).select_related('category').order_by('reference_number')
    
    # Check which non-activated bunkers have planned activations by this user
    from planned_activations.models import PlannedActivation
    user_planned_bunker_ids = PlannedActivation.objects.filter(
        user=request.user
    ).values_list('bunker_id', flat=True)
    
    # Get non-hunted bunkers (for hunter)
    hunted_bunker_ids = [b['bunker__id'] for b in hunted_bunkers]
    non_hunted_bunkers = Bunker.objects.exclude(
        id__in=hunted_bunker_ids
    ).select_related('category').order_by('reference_number')
    
    # Check which non-hunted bunkers have ANY planned activations (excluding current user's plans)
    planned_bunker_ids = PlannedActivation.objects.exclude(
        user=request.user
    ).values_list('bunker_id', flat=True).distinct()
    
    # Check which non-hunted bunkers have active spots
    from cluster.models import Spot
    from django.utils import timezone
    from datetime import timedelta
    active_spot_bunker_ids = Spot.objects.filter(
        bunker__isnull=False,
        is_active=True,
        expires_at__gte=timezone.now()  # Not expired yet
    ).values_list('bunker_id', flat=True).distinct()
    
    context = {
        'stats': stats,
        'activated_bunkers': activated_bunkers,
        'hunted_bunkers': hunted_bunkers,
        'all_activations': all_activations,
        'all_hunted_qsos': all_hunted_qsos,
        'activator_bands': activator_bands,
        'activator_modes': activator_modes,
        'hunter_bands': hunter_bands,
        'hunter_modes': hunter_modes,
        'non_activated_bunkers': non_activated_bunkers,
        'user_planned_bunker_ids': list(user_planned_bunker_ids),
        'non_hunted_bunkers': non_hunted_bunkers,
        'planned_bunker_ids': list(planned_bunker_ids),
        'active_spot_bunker_ids': list(active_spot_bunker_ids),
    }
    return render(request, 'profile.html', context)


def register_view(request):
    """User registration"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        callsign = request.POST.get('callsign')
        
        # Normalize callsign to uppercase for consistency
        if callsign:
            callsign = callsign.upper().strip()
        
        # Validation
        if not all([email, password, password2, callsign]):
            messages.error(request, _('All fields are required'))
            return redirect('register')
        
        if password != password2:
            messages.error(request, _('Passwords do not match'))
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, _('Email already registered'))
            return redirect('register')
        
        # Check if callsign exists (case-insensitive)
        existing_user = User.objects.filter(callsign__iexact=callsign).first()
        
        if existing_user:
            # If user was auto-created (from log import), allow them to "claim" the account
            if existing_user.auto_created and not existing_user.is_active:
                try:
                    # Update the auto-created account with registration details
                    existing_user.email = email
                    existing_user.set_password(password)
                    existing_user.is_active = True
                    existing_user.auto_created = False  # Now it's a proper registered account
                    existing_user.save()
                    
                    # Login user
                    login(request, existing_user)
                    messages.success(request, _('Account activated successfully! Welcome to BOTA!'))
                    messages.info(request, _('Your previous hunting activity has been linked to your account.'))
                    return redirect('dashboard')
                    
                except Exception as e:
                    messages.error(request, _(f'Error activating account: {str(e)}'))
                    return redirect('register')
            else:
                # Callsign is taken by an active/registered user
                messages.error(request, _('Callsign already taken'))
                return redirect('register')
        
        try:
            # Create new user
            user = User.objects.create_user(
                email=email,
                password=password,
                callsign=callsign,
                auto_created=False  # Explicitly mark as manually registered
            )
            
            # Login user
            login(request, user)
            messages.success(request, _('Registration successful! Welcome to BOTA!'))
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, _(f'Error creating account: {str(e)}'))
            return redirect('register')
    
    return render(request, 'register.html')


def login_view(request):
    """User login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, _('Email and password are required'))
            return redirect('login')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, _(f'Welcome back, {user.callsign}!'))
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, _('Invalid email or password'))
            return redirect('login')
    
    return render(request, 'login.html')


@login_required
def logout_view(request):
    """User logout"""
    logout(request)
    messages.success(request, _('You have been logged out successfully'))
    return redirect('home')


def cluster_view(request):
    """
    Cluster/Spotting system page (public read, authenticated write)
    Displays active spots with auto-refresh capability
    """
    from django.http import JsonResponse
    from cluster.models import Spot
    from django.utils import timezone
    
    # Handle POST request (create new spot) - requires authentication
    if request.method == 'POST' and request.user.is_authenticated:
        try:
            activator_callsign = request.POST.get('activator_callsign', '').strip().upper()
            frequency = request.POST.get('frequency', '').strip()
            bunker_reference = request.POST.get('bunker_reference', '').strip().upper()
            comment = request.POST.get('comment', '').strip()
            
            # Basic validation
            if not activator_callsign or not frequency:
                return JsonResponse({
                    'success': False,
                    'error': _('Activator callsign and frequency are required')
                }, status=400)
            
            # Create spot
            try:
                spot = Spot.objects.create(
                    activator_callsign=activator_callsign,
                    spotter=request.user,
                    frequency=float(frequency),
                    bunker_reference=bunker_reference if bunker_reference else None,
                    comment=comment if comment else '',
                    last_respot_time=timezone.now()  # Set initial spot time
                )
                
                return JsonResponse({
                    'success': True,
                    'message': _('Spot posted successfully'),
                    'spot': {
                        'id': spot.id,
                        'activator_callsign': spot.activator_callsign,
                        'frequency': str(spot.frequency),
                        'band': spot.band,
                        'bunker_reference': spot.bunker_reference or '',
                        'comment': spot.comment,
                        'spotter': spot.spotter.callsign,
                        'time_since_update': spot.time_since_update()
                    }
                })
            except ValueError as e:
                return JsonResponse({
                    'success': False,
                    'error': _('Invalid frequency value')
                }, status=400)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': _('Error processing spot: ') + str(e)
            }, status=500)
    
    # GET request - display spots
    # Get filter parameters
    activator_filter = request.GET.get('activator', '')
    spotter_filter = request.GET.get('spotter', '')
    band_filter = request.GET.get('band', '')
    
    # Get active spots (not expired)
    spots = Spot.objects.filter(
        is_active=True,
        expires_at__gt=timezone.now()
    ).select_related('spotter', 'bunker').order_by('-updated_at')
    
    # Apply filters
    if activator_filter:
        spots = spots.filter(activator_callsign__icontains=activator_filter)
    if spotter_filter:
        spots = spots.filter(spotter__callsign__icontains=spotter_filter)
    if band_filter:
        spots = spots.filter(band=band_filter)
    
    # Get unique bands for filter dropdown
    unique_bands = Spot.objects.filter(
        is_active=True,
        expires_at__gt=timezone.now()
    ).values_list('band', flat=True).distinct().order_by('band')
    
    context = {
        'spots': spots,
        'unique_bands': unique_bands,
        'activator_filter': activator_filter,
        'spotter_filter': spotter_filter,
        'band_filter': band_filter,
    }
    
    return render(request, 'cluster.html', context)


def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'privacy_policy.html')


def cookie_policy(request):
    """Cookie Policy page"""
    return render(request, 'cookie_policy.html')


def terms_of_service(request):
    """Terms of Service page"""
    return render(request, 'terms_of_service.html')


@login_required
def log_history_view(request):
    """Log upload history page with filtering"""
    from activations.models import LogUpload, ActivationLog
    from django.db.models import Q, Count
    
    # Get all uploads for current user
    uploads = LogUpload.objects.filter(user=request.user).prefetch_related('qsos')
    
    # Filters
    callsign_filter = request.GET.get('callsign', '').strip()
    bunker_ref_filter = request.GET.get('bunker_ref', '').strip()
    mode_filter = request.GET.get('mode', '').strip()
    band_filter = request.GET.get('band', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Build QSOs query for filtering
    qsos_query = ActivationLog.objects.filter(user=request.user)
    
    if callsign_filter:
        qsos_query = qsos_query.filter(
            Q(activator__callsign__icontains=callsign_filter) |
            Q(user__callsign__icontains=callsign_filter)
        )
    
    if bunker_ref_filter:
        qsos_query = qsos_query.filter(bunker__reference_number__icontains=bunker_ref_filter)
    
    if mode_filter:
        qsos_query = qsos_query.filter(mode__icontains=mode_filter)
    
    if band_filter:
        qsos_query = qsos_query.filter(band__icontains=band_filter)
    
    if date_from:
        from datetime import datetime
        qsos_query = qsos_query.filter(activation_date__gte=datetime.strptime(date_from, '%Y-%m-%d'))
    
    if date_to:
        from datetime import datetime
        qsos_query = qsos_query.filter(activation_date__lte=datetime.strptime(date_to, '%Y-%m-%d'))
    
    filtered_qso_count = qsos_query.count()
    
    # Get unique values for filters
    unique_modes = ActivationLog.objects.filter(user=request.user).exclude(mode='').values_list('mode', flat=True).distinct().order_by('mode')
    unique_bands = ActivationLog.objects.filter(user=request.user).exclude(band='').values_list('band', flat=True).distinct().order_by('band')
    
    # Get QSOs grouped by upload
    uploads_with_qsos = {}
    for upload in uploads:
        upload_qsos = upload.qsos.all().order_by('-activation_date')
        
        # Apply filters to this upload's QSOs
        if callsign_filter or bunker_ref_filter or mode_filter or band_filter or date_from or date_to:
            filtered_upload_qsos = upload_qsos
            
            if callsign_filter:
                filtered_upload_qsos = filtered_upload_qsos.filter(
                    Q(activator__callsign__icontains=callsign_filter) |
                    Q(user__callsign__icontains=callsign_filter)
                )
            
            if bunker_ref_filter:
                filtered_upload_qsos = filtered_upload_qsos.filter(bunker__reference_number__icontains=bunker_ref_filter)
            
            if mode_filter:
                filtered_upload_qsos = filtered_upload_qsos.filter(mode__icontains=mode_filter)
            
            if band_filter:
                filtered_upload_qsos = filtered_upload_qsos.filter(band__icontains=band_filter)
            
            if date_from:
                from datetime import datetime
                filtered_upload_qsos = filtered_upload_qsos.filter(activation_date__gte=datetime.strptime(date_from, '%Y-%m-%d'))
            
            if date_to:
                from datetime import datetime
                filtered_upload_qsos = filtered_upload_qsos.filter(activation_date__lte=datetime.strptime(date_to, '%Y-%m-%d'))
            
            uploads_with_qsos[upload.id] = filtered_upload_qsos
        else:
            uploads_with_qsos[upload.id] = upload_qsos
    
    context = {
        'uploads': uploads,
        'uploads_with_qsos': uploads_with_qsos,
        'filtered_qso_count': filtered_qso_count,
        'callsign_filter': callsign_filter,
        'bunker_ref_filter': bunker_ref_filter,
        'mode_filter': mode_filter,
        'band_filter': band_filter,
        'date_from': date_from,
        'date_to': date_to,
        'unique_modes': unique_modes,
        'unique_bands': unique_bands,
    }
    
    return render(request, 'log_history.html', context)


def map_view(request):
    """
    Interactive map showing all bunkers with color-coded markers.
    
    For anonymous users: Simple markers
    For logged-in users: Color-coded by activation/hunted status:
      - Gray: Not activated, not hunted
      - Blue: Not activated, hunted
      - Green: Activated, not hunted  
      - Gold: Activated AND hunted
      - Orange: Currently being activated (active spot)
    """
    from bunkers.models import Bunker
    from activations.models import ActivationLog
    from cluster.models import Spot
    from django.db.models import Q
    from django.utils import timezone
    import json
    
    # Get all verified bunkers with coordinates
    bunkers = Bunker.objects.filter(
        is_verified=True,
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related().order_by('reference_number')
    
    # Get active spots (not expired)
    active_spot_bunker_ids = set(
        Spot.objects.filter(
            is_active=True,
            expires_at__gt=timezone.now(),
            bunker__isnull=False
        ).values_list('bunker_id', flat=True).distinct()
    )
    
    bunkers_data = []
    
    if request.user.is_authenticated:
        # Get user's activated and hunted bunkers
        activated_bunker_ids = set(
            ActivationLog.objects.filter(activator=request.user)
            .values_list('bunker_id', flat=True)
            .distinct()
        )
        
        hunted_bunker_ids = set(
            ActivationLog.objects.filter(user=request.user)
            .values_list('bunker_id', flat=True)
            .distinct()
        )
        
        for bunker in bunkers:
            is_activated = bunker.id in activated_bunker_ids
            is_hunted = bunker.id in hunted_bunker_ids
            is_under_activation = bunker.id in active_spot_bunker_ids
            
            # Determine color based on status (ignore under_activation for color)
            if is_activated and is_hunted:
                color = 'gold'  # Both activated and hunted
                icon = 'trophy'
            elif is_activated:
                color = 'green'  # Only activated
                icon = 'broadcast'
            elif is_hunted:
                color = 'blue'  # Only hunted
                icon = 'binoculars'
            else:
                color = 'gray'  # Neither
                icon = 'geo-alt'
            
            # If under activation, add orange border via CSS animation
            # (handled in frontend with is_under_activation flag)
            
            bunkers_data.append({
                'id': bunker.id,
                'reference': bunker.reference_number,
                'name': bunker.name_en,
                'lat': float(bunker.latitude),
                'lng': float(bunker.longitude),
                'color': color,
                'icon': icon,
                'is_activated': is_activated,
                'is_hunted': is_hunted,
                'is_under_activation': is_under_activation,
            })
    else:
        # Anonymous user - simple markers
        for bunker in bunkers:
            is_under_activation = bunker.id in active_spot_bunker_ids
            
            bunkers_data.append({
                'id': bunker.id,
                'reference': bunker.reference_number,
                'name': bunker.name_en,
                'lat': float(bunker.latitude),
                'lng': float(bunker.longitude),
                'color': 'red',  # Default red for anonymous
                'icon': 'geo-alt',
                'is_activated': False,
                'is_hunted': False,
                'is_under_activation': is_under_activation,
            })
    
    context = {
        'bunkers_json': json.dumps(bunkers_data),
        'bunkers_count': len(bunkers_data),
    }
    
    return render(request, 'map.html', context)


@login_required
def change_password_required(request):
    """Force password change view for users with force_password_change=True"""
    from django.contrib.auth.forms import SetPasswordForm
    
    # If user doesn't need to change password, redirect to dashboard
    if not request.user.force_password_change:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = SetPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Clear force_password_change flag
            user.force_password_change = False
            user.save()
            
            # Update session to prevent logout
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            
            messages.success(request, _('Your password has been changed successfully!'))
            return redirect('dashboard')
    else:
        form = SetPasswordForm(request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'change_password_required.html', context)
