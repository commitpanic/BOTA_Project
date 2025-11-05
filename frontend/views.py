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
    
    # Get recent activity
    recent_logs = ActivationLog.objects.filter(
        user=request.user
    ).select_related('activation_key__bunker').order_by('-activation_date')[:10]
    
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
    """Download diploma certificate as PDF"""
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Frame, PageTemplate
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.pdfgen import canvas as pdfcanvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import qrcode
    import io
    from django.utils.translation import get_language
    
    # Get the diploma (ensure user owns it)
    diploma = get_object_or_404(Diploma, id=diploma_id, user=request.user)
    
    # Create PDF in memory
    buffer = io.BytesIO()
    
    # Register Lato fonts (supports Polish characters)
    try:
        import os
        from pathlib import Path
        from django.conf import settings
        
        # Path to Lato fonts in static/fonts
        fonts_dir = Path(settings.BASE_DIR) / 'static' / 'fonts'
        
        lato_regular = fonts_dir / 'Lato-Regular.ttf'
        lato_bold = fonts_dir / 'Lato-Bold.ttf'
        lato_italic = fonts_dir / 'Lato-Italic.ttf'
        
        # Register Lato fonts if they exist
        if lato_regular.exists() and lato_bold.exists() and lato_italic.exists():
            pdfmetrics.registerFont(TTFont('Lato', str(lato_regular)))
            pdfmetrics.registerFont(TTFont('Lato-Bold', str(lato_bold)))
            pdfmetrics.registerFont(TTFont('Lato-Italic', str(lato_italic)))
            default_font = 'Lato'
            bold_font = 'Lato-Bold'
            italic_font = 'Lato-Italic'
        else:
            # Fallback to Helvetica
            default_font = 'Helvetica'
            bold_font = 'Helvetica-Bold'
            italic_font = 'Helvetica-Oblique'
    except Exception as e:
        # Fallback to Helvetica on any error
        default_font = 'Helvetica'
        bold_font = 'Helvetica-Bold'
        italic_font = 'Helvetica-Oblique'
    
    # Custom page template with border
    def add_page_decorations(canvas, doc):
        """Add decorative border to each page"""
        canvas.saveState()
        # Draw border
        canvas.setStrokeColor(colors.HexColor('#1a5490'))
        canvas.setLineWidth(3)
        canvas.rect(1.5*cm, 1.5*cm, 26*cm, 17.5*cm, stroke=1, fill=0)
        canvas.restoreState()
    
    # Create the PDF object using landscape A4
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=2.5*cm,
        leftMargin=2.5*cm,
        topMargin=2.5*cm,
        bottomMargin=2.5*cm
    )
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles with Unicode-supporting fonts
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=15,
        alignment=TA_CENTER,
        fontName=bold_font
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=bold_font
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=default_font
    )
    
    info_style = ParagraphStyle(
        'CustomInfo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.grey,
        alignment=TA_CENTER,
        fontName=default_font
    )
    
    # Determine language
    current_lang = get_language()
    is_polish = current_lang == 'pl'
    
    # Get diploma names and descriptions
    diploma_name = diploma.diploma_type.name_pl if is_polish else diploma.diploma_type.name_en
    diploma_desc = diploma.diploma_type.description_pl if is_polish else diploma.diploma_type.description_en
    
    # Title
    if is_polish:
        title_text = "CERTYFIKAT DYPLOMU"
    else:
        title_text = "DIPLOMA CERTIFICATE"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Subtitle - Program name
    program_text = "BOTA - Bunkers On The Air"
    elements.append(Paragraph(program_text, subtitle_style))
    elements.append(Spacer(1, 0.6*cm))
    
    # Award text
    if is_polish:
        award_text = "Niniejszym certyfikuje się, że"
    else:
        award_text = "This certifies that"
    elements.append(Paragraph(award_text, body_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Callsign (large and bold)
    callsign_style = ParagraphStyle(
        'Callsign',
        parent=styles['Normal'],
        fontSize=22,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=bold_font
    )
    elements.append(Paragraph(diploma.user.callsign, callsign_style))
    elements.append(Spacer(1, 0.4*cm))
    
    # Achievement text
    if is_polish:
        achievement_text = f"osiągnął wymagania dla dyplomu"
    else:
        achievement_text = f"has achieved the requirements for the"
    elements.append(Paragraph(achievement_text, body_style))
    elements.append(Spacer(1, 0.3*cm))
    
    # Diploma name (highlighted)
    diploma_name_style = ParagraphStyle(
        'DiplomaName',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#d4af37'),  # Gold color
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName=bold_font
    )
    elements.append(Paragraph(diploma_name, diploma_name_style))
    
    # Description
    if diploma_desc:
        elements.append(Spacer(1, 0.2*cm))
        desc_style = ParagraphStyle(
            'Description',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER,
            fontName=italic_font
        )
        elements.append(Paragraph(diploma_desc, desc_style))
    
    elements.append(Spacer(1, 0.6*cm))
    
    # Requirements met - show minimum required points
    req_text_parts = []
    if diploma.diploma_type.min_activator_points > 0:
        if is_polish:
            req_text_parts.append(f"Zdobyto wymaganą liczbę punktów: {diploma.diploma_type.min_activator_points} (aktywator)")
        else:
            req_text_parts.append(f"Required points achieved: {diploma.diploma_type.min_activator_points} (activator)")
    if diploma.diploma_type.min_hunter_points > 0:
        if is_polish:
            req_text_parts.append(f"Zdobyto wymaganą liczbę punktów: {diploma.diploma_type.min_hunter_points} (łowca)")
        else:
            req_text_parts.append(f"Required points achieved: {diploma.diploma_type.min_hunter_points} (hunter)")
    if diploma.diploma_type.min_b2b_points > 0:
        if is_polish:
            req_text_parts.append(f"Zdobyto wymaganą liczbę punktów: {diploma.diploma_type.min_b2b_points} (B2B)")
        else:
            req_text_parts.append(f"Required points achieved: {diploma.diploma_type.min_b2b_points} (B2B)")
    
    if req_text_parts:
        req_text = " • ".join(req_text_parts)
        elements.append(Paragraph(req_text, info_style))
        elements.append(Spacer(1, 0.3*cm))
    
    # Certificate info table (removed verification code row)
    if is_polish:
        info_data = [
            ['Numer dyplomu:', diploma.diploma_number],
            ['Data wydania:', diploma.issue_date.strftime('%Y-%m-%d')],
        ]
    else:
        info_data = [
            ['Diploma Number:', diploma.diploma_number],
            ['Issue Date:', diploma.issue_date.strftime('%Y-%m-%d')],
        ]
    
    info_table = Table(info_data, colWidths=[6*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), bold_font),
        ('FONTNAME', (1, 0), (1, -1), default_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.grey),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.6*cm))
    
    # Generate QR code for verification
    verification_url = request.build_absolute_uri(f'/verify-diploma/{diploma.diploma_number}/')
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(verification_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR code to buffer
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Add QR code to PDF (without text label, just the code)
    qr_image = Image(qr_buffer, width=3*cm, height=3*cm)
    
    # Center the QR code in a table
    qr_table = Table(
        [[qr_image]],
        colWidths=[3*cm]
    )
    qr_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(qr_table)
    
    # Build PDF with custom page decorations
    doc.build(elements, onFirstPage=add_page_decorations, onLaterPages=add_page_decorations)
    
    # Get PDF from buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="BOTA_Diploma_{diploma.diploma_number}.pdf"'
    response.write(pdf)
    
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
                    comment=comment if comment else ''
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
