"""
Frontend views for BOTA Project
Handles user-facing pages with i18n support
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Count, Sum
from django.utils.translation import gettext as _
from accounts.models import User, UserStatistics
from bunkers.models import Bunker
from activations.models import ActivationLog
from diplomas.models import Diploma, DiplomaProgress


def home(request):
    """Home page with program statistics"""
    
    # Get recent activations grouped by activator, bunker, and date
    # Show activators with their QSO count for each activation
    from django.db.models import Count, Max
    
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
        'recent_activations': recent_activations,
    }
    return render(request, 'home.html', context)


@login_required
def dashboard(request):
    """User dashboard with statistics and progress"""
    # Get or create user statistics
    stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    # Get diploma progress
    diploma_progress = DiplomaProgress.objects.filter(
        user=request.user
    ).select_related('diploma_type').order_by('-percentage_complete')[:6]
    
    # Get recent activity
    recent_logs = ActivationLog.objects.filter(
        user=request.user
    ).select_related('activation_key__bunker').order_by('-activation_date')[:10]
    
    context = {
        'stats': stats,
        'diploma_progress': diploma_progress,
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
            result = service.process_adif_upload(content, request.user)
            
            # Check if successful
            if not result.get('success'):
                errors = result.get('errors', ['Unknown error'])
                for error in errors:
                    messages.error(request, error)
                return redirect('upload_log')
            
            # Show success message
            messages.success(
                request,
                _(f'Successfully processed {result["qsos_processed"]} QSOs from {result["bunker"]}. '
                  f'Updated {result["hunters_updated"]} hunters. '
                  f'B2B QSOs: {result["b2b_qsos"]}')
            )
            
            # Show warnings if any
            for warning in result.get('warnings', []):
                messages.warning(request, warning)
            
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, _(f'Error processing file: {str(e)}'))
            return redirect('upload_log')
    
    return render(request, 'upload_log.html')


@login_required
def diplomas_view(request):
    """User diplomas and progress"""
    # Get earned diplomas
    earned_diplomas = Diploma.objects.filter(
        user=request.user
    ).select_related('diploma_type').order_by('-issue_date')
    
    # Get all diploma progress
    all_progress = DiplomaProgress.objects.filter(
        user=request.user
    ).select_related('diploma_type').order_by('diploma_type__category', 'diploma_type__display_order')
    
    context = {
        'earned_diplomas': earned_diplomas,
        'all_progress': all_progress,
    }
    return render(request, 'diplomas.html', context)


@login_required
def download_certificate(request, diploma_id):
    """Download diploma certificate as PDF"""
    from django.http import HttpResponse
    
    # Get the diploma (ensure user owns it)
    diploma = get_object_or_404(Diploma, id=diploma_id, user=request.user)
    
    # For now, return a simple message
    # TODO: Generate PDF certificate using reportlab or similar
    return HttpResponse(
        f"Certificate download for {diploma.diploma_type.name_en} - {diploma.diploma_number}\n"
        f"Awarded to: {diploma.user.callsign}\n"
        f"Date: {diploma.issue_date}\n\n"
        f"[PDF generation coming soon]",
        content_type='text/plain'
    )


@login_required
def profile_view(request):
    """User profile page"""
    stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    context = {
        'stats': stats,
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
        
        if User.objects.filter(callsign=callsign).exists():
            messages.error(request, _('Callsign already taken'))
            return redirect('register')
        
        try:
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password,
                callsign=callsign
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
