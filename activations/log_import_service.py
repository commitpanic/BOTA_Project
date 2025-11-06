"""
Service for processing ADIF log imports and updating user statistics.
Handles activator log uploads and hunter point calculations.
"""
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from typing import Dict, List
from decimal import Decimal

from .adif_parser import ADIFParser
from .models import ActivationLog, ActivationKey
from bunkers.models import Bunker
from accounts.models import UserStatistics

User = get_user_model()


class LogImportService:
    """Service for importing ADIF logs and processing activations"""
    
    def __init__(self):
        self.parser = None
        self.bunker = None
        self.activator = None
        self.errors = []
        self.warnings = []
    
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
        
        # Create LogUpload record
        log_upload = LogUpload.objects.create(
            user=uploader_user,
            filename=filename or 'unknown.adi',
            file_format='ADIF',
            status='processing'
        )
        self.log_upload = log_upload
        
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
        
        # Update activator statistics
        self._update_activator_stats(qsos_processed, b2b_qsos)
        
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
            'log_upload_id': log_upload.id
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
            
            # Check for duplicate log entry
            existing = ActivationLog.objects.filter(
                user=hunter_user,
                bunker=self.bunker,
                activator=self.activator,
                activation_date=qso_datetime
            ).exists()
            
            if existing:
                # Silently skip duplicates - don't show warnings
                return {
                    'success': False, 
                    'error': None,  # No error message for duplicates
                    'duplicate': True
                }
            
            # Create activation log entry
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
            
            # Award points to ACTIVATOR (person who uploaded the log = person who was at the bunker)
            self._award_activator_points(self.activator)
            
            # Award points to HUNTER (person who worked the bunker = person in the log)
            self._award_hunter_points(hunter_user)
            
            # Check if B2B can be confirmed (both logs uploaded)
            if is_b2b:
                self._check_and_award_b2b(self.activator, hunter_user, qso_datetime)
            
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
    
    def _award_hunter_points(self, hunter_user: User):
        """
        Award points to hunter for working a bunker
        
        Args:
            hunter_user: Hunter User object (person who worked the bunker)
        """
        stats, _ = UserStatistics.objects.get_or_create(user=hunter_user)
        
        # Hunter gets 1 point per QSO with a bunker
        stats.hunter_points += 1
        stats.total_hunter_qso += 1
        
        # Update unique bunkers hunted count
        unique_bunkers = ActivationLog.objects.filter(
            user=hunter_user
        ).values('bunker').distinct().count()
        stats.unique_bunkers_hunted = unique_bunkers
        
        stats.save()
    
    def _award_activator_points(self, activator_user: User):
        """
        Award points to activator for making QSO from bunker
        
        Args:
            activator_user: Activator User object (person who was at the bunker)
        """
        stats, _ = UserStatistics.objects.get_or_create(user=activator_user)
        
        # Activator gets 1 point per QSO made from bunker
        stats.activator_points += 1
        stats.total_activator_qso += 1
        
        stats.save()
    
    def _check_and_award_b2b(self, activator: User, hunter: User, qso_datetime):
        """
        Check if B2B can be confirmed (both logs uploaded) and award points
        
        B2B is only confirmed when:
        1. Activator A uploads log showing they worked Activator B
        2. Activator B uploads log showing they worked Activator A
        3. Both QSOs are within reasonable time window (±30 minutes)
        
        Args:
            activator: The activator who just uploaded their log
            hunter: The hunter in the log (who might also be an activator)
            qso_datetime: The datetime of this QSO
        """
        from django.utils import timezone
        from datetime import timedelta
        
        # Check if the "hunter" has also uploaded a log showing they worked this activator
        # Look for a reciprocal QSO within ±30 minutes
        time_window_start = qso_datetime - timedelta(minutes=30)
        time_window_end = qso_datetime + timedelta(minutes=30)
        
        # Find reciprocal log: hunter was activator, current activator was in their log
        reciprocal_log = ActivationLog.objects.filter(
            activator=hunter,  # Hunter was the activator
            user=activator,    # Current activator was in their log
            activation_date__gte=time_window_start,
            activation_date__lte=time_window_end,
            is_b2b=True  # They also marked it as B2B
        ).first()
        
        if reciprocal_log:
            # B2B confirmed! Award points to both
            activator_stats, _ = UserStatistics.objects.get_or_create(user=activator)
            hunter_stats, _ = UserStatistics.objects.get_or_create(user=hunter)
            
            # Check if we haven't already counted this B2B pair
            # (to avoid double-counting if logs are uploaded multiple times)
            current_log = ActivationLog.objects.get(
                activator=activator,
                user=hunter,
                activation_date=qso_datetime
            )
            
            # Mark both logs as B2B confirmed
            if not hasattr(current_log, 'b2b_confirmed') or not current_log.b2b_confirmed:
                # Award B2B points - each confirmed B2B gives 1 point
                activator_stats.activator_b2b_qso += 1
                activator_stats.b2b_points += 1
                activator_stats.total_b2b_qso += 1
                activator_stats.save()
                
                hunter_stats.activator_b2b_qso += 1
                hunter_stats.b2b_points += 1
                hunter_stats.total_b2b_qso += 1
                hunter_stats.save()
                
                self.warnings.append(
                    f"B2B confirmed between {activator.callsign} and {hunter.callsign}!"
                )
    
    def _update_activator_stats(self, qso_count: int, b2b_count: int):
        """
        Update activator-specific statistics
        
        Args:
            qso_count: Total QSOs processed
            b2b_count: Number of B2B QSOs
        """
        stats, _ = UserStatistics.objects.get_or_create(user=self.activator)
        
        # Update unique bunkers activated
        unique_activations = ActivationLog.objects.filter(
            activator=self.activator
        ).values('bunker').distinct().count()
        stats.unique_activations = unique_activations
        
        stats.save()
    
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
