"""
Service for processing ADIF log imports and updating user statistics.
Handles activator log uploads and hunter point calculations.
"""
import hashlib
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from typing import Dict, List
from decimal import Decimal

from .adif_parser import ADIFParser
from .models import ActivationLog, ActivationKey
from bunkers.models import Bunker
from accounts.models import UserStatistics
from accounts.points_service import PointsService

User = get_user_model()


class LogImportService:
    """Service for importing ADIF logs and processing activations"""
    
    def __init__(self):
        self.parser = None
        self.bunker = None
        self.activator = None
        self.errors = []
        self.warnings = []
        self.transactions = []  # Track all point transactions for batch creation
    
    @transaction.atomic
    def process_adif_upload(self, file_content: str, uploader_user: User, filename: str = None) -> Dict:
        """
        Process uploaded ADIF file
        
        Args:
            file_content: Content of .adi file as string
            uploader_user: User uploading the file
            filename: Optional filename for logging
            
        Returns:
            Dictionary with processing results
        """
        from .models import LogUpload
        
        # Calculate file checksum for duplicate detection
        file_checksum = hashlib.sha256(file_content.encode('utf-8')).hexdigest()
        
        # Check for duplicate upload
        existing_upload = LogUpload.objects.filter(
            file_checksum=file_checksum,
            user=uploader_user
        ).first()
        
        if existing_upload:
            return {
                'success': False,
                'errors': [f'This file was already uploaded on {existing_upload.uploaded_at.strftime("%Y-%m-%d %H:%M")}'],
                'qsos_processed': 0,
                'hunters_updated': 0,
                'duplicate_upload': True
            }
        
        # Create LogUpload record
        log_upload = LogUpload.objects.create(
            user=uploader_user,
            filename=filename or 'unknown.adi',
            file_format='ADIF',
            file_checksum=file_checksum,
            status='processing'
        )
        self.log_upload = log_upload
        self.transactions = []  # Reset transactions list
        
        # Parse ADIF file
        self.parser = ADIFParser(file_content)
        parse_result = self.parser.parse()
        
        # Validate
        validation = self.parser.validate()
        if not validation['valid']:
            log_upload.status = 'failed'
            log_upload.error_message = '; '.join(validation['errors'])
            log_upload.save()
            return {
                'success': False,
                'errors': validation['errors'],
                'qsos_processed': 0,
                'hunters_updated': 0
            }
        
        # Extract key information
        bunker_ref = self.parser.extract_bunker_reference()
        activator_callsign = self.parser.extract_activator_callsign()
        
        # Verify bunker exists
        try:
            self.bunker = Bunker.objects.get(reference_number=bunker_ref)
        except Bunker.DoesNotExist:
            log_upload.status = 'failed'
            log_upload.error_message = f"Bunker {bunker_ref} not found in database"
            log_upload.save()
            return {
                'success': False,
                'errors': [f"Bunker {bunker_ref} not found in database"],
                'qsos_processed': 0,
                'hunters_updated': 0
            }
        
        # Verify activator user
        try:
            self.activator = User.objects.get(callsign=activator_callsign)
        except User.DoesNotExist:
            # Create user if doesn't exist (optional - could require pre-registration)
            log_upload.status = 'failed'
            log_upload.error_message = f"Activator user {activator_callsign} not found"
            log_upload.save()
            return {
                'success': False,
                'errors': [f"Activator user {activator_callsign} not found. Please register first."],
                'qsos_processed': 0,
                'hunters_updated': 0
            }
        
        # Verify uploader is the activator (security check)
        if uploader_user.callsign != activator_callsign and not uploader_user.is_staff:
            log_upload.status = 'failed'
            log_upload.error_message = "Security: You can only upload logs for your own callsign"
            log_upload.save()
            return {
                'success': False,
                'errors': [f"You can only upload logs for your own callsign ({uploader_user.callsign})"],
                'qsos_processed': 0,
                'hunters_updated': 0
            }
        
        # Process QSOs
        qsos_processed = 0
        qsos_duplicates = 0
        hunters_updated = set()
        b2b_qsos = 0
        
        for qso in self.parser.qsos:
            result = self._process_qso(qso)
            if result['success']:
                qsos_processed += 1
                if result.get('hunter_callsign'):
                    hunters_updated.add(result['hunter_callsign'])
                if result.get('is_b2b'):
                    b2b_qsos += 1
            else:
                # Only add warning if there's an actual error (not duplicate)
                if result.get('error'):
                    self.warnings.append(result['error'])
                elif result.get('duplicate'):
                    qsos_duplicates += 1
        
        # Create points transaction batch for audit trail
        if self.transactions:
            batch = PointsService.create_batch(
                name=f"Log import: {filename or 'unknown.adi'}",
                transactions=self.transactions,
                log_upload=log_upload,
                created_by=uploader_user
            )
            log_upload.points_batch = batch
        
        # Update diploma progress for activator
        self._update_diploma_progress(self.activator)
        
        # Update diploma progress for all hunters
        for hunter_callsign in hunters_updated:
            try:
                hunter = User.objects.get(callsign=hunter_callsign)
                self._update_diploma_progress(hunter)
            except User.DoesNotExist:
                pass
        
        # Update LogUpload with final statistics
        total_qsos = qsos_processed + qsos_duplicates
        log_upload.qso_count = total_qsos
        log_upload.processed_qso_count = qsos_processed
        log_upload.status = 'completed'
        log_upload.save()
        
        return {
            'success': True,
            'qsos_processed': qsos_processed,
            'qsos_duplicates': qsos_duplicates,
            'hunters_updated': len(hunters_updated),
            'b2b_qsos': b2b_qsos,
            'bunker': bunker_ref,
            'activator': activator_callsign,
            'warnings': self.warnings,
            'errors': [],
            'log_upload_id': log_upload.id,
            'batch_id': batch.id if self.transactions else None
        }
    
    def _process_qso(self, qso: Dict) -> Dict:
        """
        Process individual QSO record
        
        Args:
            qso: Parsed QSO dictionary
            
        Returns:
            Result dictionary
        """
        try:
            hunter_callsign = qso.get('CALL', '').strip().upper()
            if not hunter_callsign:
                return {'success': False, 'error': 'Missing callsign'}
            
            # Parse QSO datetime
            qso_datetime = self.parser.parse_qso_datetime(qso)
            if not qso_datetime:
                return {'success': False, 'error': f'Invalid date/time for {hunter_callsign}'}
            
            # Check if B2B
            is_b2b = self.parser.is_b2b_qso(qso)
            
            # Get or create hunter user
            hunter_user, created = User.objects.get_or_create(
                callsign=hunter_callsign,
                defaults={
                    'email': f'{hunter_callsign.lower()}@temp.bota.invalid',  # Temporary email
                    'is_active': False,  # Inactive until they register properly
                    'auto_created': True  # Mark as auto-created from log import
                }
            )
            
            # Note: Placeholder accounts are created silently - no need to inform user
            
            # Create activation log entry (unique_together will prevent duplicates at DB level)
            try:
                log = ActivationLog.objects.create(
                    user=hunter_user,
                    bunker=self.bunker,
                    activator=self.activator,
                    activation_date=qso_datetime,
                    is_b2b=is_b2b,
                    mode=self.parser.get_qso_mode(qso),
                    band=self.parser.get_qso_band(qso),
                    notes=f"Imported from ADIF log",
                    verified=True,  # Auto-verify activator-uploaded logs
                    log_upload=self.log_upload  # Link to upload batch
                )
            except Exception as e:
                # Catch IntegrityError from unique_together constraint
                if 'UNIQUE constraint failed' in str(e) or 'duplicate key' in str(e).lower():
                    # Silently skip duplicates
                    return {
                        'success': False,
                        'error': None,
                        'duplicate': True
                    }
                else:
                    # Re-raise other exceptions
                    raise
            
            # Award points to ACTIVATOR using PointsService
            activator_tx = PointsService.award_activator_points(
                user=self.activator,
                activation_log=log,
                created_by=self.activator
            )
            if activator_tx:
                self.transactions.append(activator_tx)
            
            # Award points to HUNTER using PointsService
            hunter_tx = PointsService.award_hunter_points(
                user=hunter_user,
                activation_log=log,
                created_by=self.activator
            )
            if hunter_tx:
                self.transactions.append(hunter_tx)
            
            # Check if B2B can be confirmed (both logs uploaded)
            if is_b2b:
                self._check_and_award_b2b(self.activator, hunter_user, log)
            
            return {
                'success': True,
                'hunter_callsign': hunter_callsign,
                'is_b2b': is_b2b,
                'log_id': log.id
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Error processing QSO: {str(e)}'
            }
    
    def _check_and_award_b2b(self, activator: User, hunter: User, current_log: ActivationLog):
        """
        Check if B2B can be confirmed (both logs uploaded) and award points using PointsService.
        
        B2B is only confirmed when:
        1. Activator A uploads log showing they worked Activator B
        2. Activator B uploads log showing they worked Activator A
        3. Both QSOs are within reasonable time window (±30 minutes)
        
        Args:
            activator: The activator who just uploaded their log
            hunter: The hunter in the log (who might also be an activator)
            current_log: The ActivationLog just created
        """
        from datetime import timedelta
        
        qso_datetime = current_log.activation_date
        
        # Look for reciprocal log within ±30 minutes
        time_window_start = qso_datetime - timedelta(minutes=30)
        time_window_end = qso_datetime + timedelta(minutes=30)
        
        # Find reciprocal log: hunter was activator, current activator was in their log
        reciprocal_log = ActivationLog.objects.filter(
            activator=hunter,  # Hunter was the activator
            user=activator,    # Current activator was in their log
            bunker=current_log.bunker,  # Same bunker
            activation_date__gte=time_window_start,
            activation_date__lte=time_window_end,
            is_b2b=True  # They also marked it as B2B
        ).first()
        
        if reciprocal_log:
            # Try to confirm B2B using PointsService
            tx1, tx2 = PointsService.confirm_b2b(
                log1=current_log,
                log2=reciprocal_log,
                created_by=activator
            )
            
            if tx1 and tx2:
                # B2B confirmed! Add transactions to batch
                self.transactions.append(tx1)
                self.transactions.append(tx2)
                
                self.warnings.append(
                    f"✅ B2B confirmed between {activator.callsign} and {hunter.callsign}!"
                )
    
    
    def _update_diploma_progress(self, user: User):
        """
        Update diploma progress for user after statistics change
        
        Args:
            user: User to update diploma progress for
        """
        from diplomas.models import DiplomaType, DiplomaProgress, Diploma
        from django.db.models.functions import TruncDate
        
        # Get user's current statistics
        stats, _ = UserStatistics.objects.get_or_create(user=user)
        
        # Calculate total activations = distinct (bunker, date) combinations
        # Each activation session counts as one, regardless of QSO count
        total_activations = ActivationLog.objects.filter(
            activator=user
        ).annotate(
            activation_day=TruncDate('activation_date')
        ).values('bunker', 'activation_day').distinct().count()
        
        # Calculate unique hunted bunkers
        unique_hunted = ActivationLog.objects.filter(
            user=user
        ).exclude(activator=user).values('bunker').distinct().count()
        
        # Get or create progress records for all active diplomas
        active_diplomas = DiplomaType.objects.filter(is_active=True)
        
        for diploma_type in active_diplomas:
            # Skip time-limited diplomas that are not currently valid
            if diploma_type.is_time_limited() and not diploma_type.is_currently_valid():
                continue
            
            progress, created = DiplomaProgress.objects.get_or_create(
                user=user,
                diploma_type=diploma_type
            )
            
            # Update points and bunker counts based on user statistics
            # Points: Each activation session = 1 activator point (distinct bunker+date)
            #         Each QSO hunting bunkers = 1 hunter point
            #         Each B2B QSO = 1 B2B point
            # Counts: Unique bunkers and distinct (bunker, date) activation sessions
            progress.update_points(
                activator=total_activations,                     # Total activation sessions (bunker+date)
                hunter=stats.total_hunter_qso,                  # Total QSOs hunting bunkers
                b2b=stats.activator_b2b_qso,                    # Total B2B QSOs
                unique_activations=stats.unique_activations,     # Unique bunkers activated
                total_activations=total_activations,             # Total activation sessions (bunker+date)
                unique_hunted=unique_hunted,                     # Unique bunkers hunted
                total_hunted=unique_hunted                       # Total hunted (same as unique for hunters)
            )
            
            # Check if eligible and not already awarded
            if progress.is_eligible:
                existing = Diploma.objects.filter(
                    user=user,
                    diploma_type=diploma_type
                ).exists()
                
                if not existing:
                    # Automatically issue diploma
                    Diploma.objects.create(
                        diploma_type=diploma_type,
                        user=user,
                        activator_points_earned=progress.activator_points,
                        hunter_points_earned=progress.hunter_points,
                        b2b_points_earned=progress.b2b_points
                    )
