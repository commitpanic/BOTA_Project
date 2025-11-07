"""
Points awarding service - handles all point transactions.
Single responsibility: Create PointsTransaction records.
"""
from django.db import transaction
from django.utils import timezone
from accounts.models import PointsTransaction, PointsTransactionBatch, UserStatistics
from activations.models import ActivationLog
import logging

logger = logging.getLogger(__name__)


class PointsService:
    """
    Service for awarding points to users.
    All point changes MUST go through this service.
    """
    
    @staticmethod
    @transaction.atomic
    def award_activator_points(user, activation_log, created_by=None):
        """
        Award points to activator for making a QSO from a bunker.
        
        Args:
            user: User who was activator
            activation_log: ActivationLog instance
            created_by: User or system that triggered this (for audit)
            
        Returns:
            PointsTransaction instance or None if already awarded
        """
        # Check if points already awarded
        if activation_log.points_awarded:
            logger.warning(
                f"Points already awarded for ActivationLog {activation_log.id}"
            )
            return None
        
        # Create transaction
        pts_transaction = PointsTransaction.objects.create(
            user=user,
            transaction_type=PointsTransaction.ACTIVATOR_QSO,
            activator_points=1,  # 1 point per QSO
            activation_log=activation_log,
            bunker=activation_log.bunker,
            reason=f"Activator QSO from {activation_log.bunker.reference_number}",
            notes=f"Mode: {activation_log.mode}, Band: {activation_log.band}",
            created_by=created_by
        )
        
        # Mark log as processed
        activation_log.points_awarded = True
        activation_log.points_transaction = pts_transaction
        activation_log.save(update_fields=['points_awarded', 'points_transaction'])
        
        # Update cached counts (not points - those are auto-updated by transaction)
        stats, _ = UserStatistics.objects.get_or_create(user=user)
        stats.total_activator_qso += 1
        
        # Update unique activations count
        stats.unique_activations = ActivationLog.objects.filter(
            activator=user
        ).values('bunker').distinct().count()
        
        stats.save(update_fields=['total_activator_qso', 'unique_activations'])
        
        logger.info(
            f"Awarded 1 activator point to {user.callsign} "
            f"(ActivationLog {activation_log.id})"
        )
        
        return pts_transaction
    
    @staticmethod
    @transaction.atomic
    def award_hunter_points(user, activation_log, created_by=None):
        """
        Award points to hunter for working a bunker.
        
        Args:
            user: User who was hunter (in the log)
            activation_log: ActivationLog instance
            created_by: User or system that triggered this
            
        Returns:
            PointsTransaction instance or None if user is same as activator
        """
        # Don't award hunter points if user is the activator
        if user == activation_log.activator:
            return None
        
        # Check if this specific hunter already has points for this QSO
        # (different from points_awarded which is for activator)
        existing = PointsTransaction.objects.filter(
            user=user,
            activation_log=activation_log,
            transaction_type=PointsTransaction.HUNTER_QSO
        ).exists()
        
        if existing:
            logger.warning(
                f"Hunter points already awarded to {user.callsign} "
                f"for ActivationLog {activation_log.id}"
            )
            return None
        
        # Create transaction
        pts_transaction = PointsTransaction.objects.create(
            user=user,
            transaction_type=PointsTransaction.HUNTER_QSO,
            hunter_points=1,  # 1 point per QSO
            activation_log=activation_log,
            bunker=activation_log.bunker,
            reason=f"Hunter QSO with {activation_log.bunker.reference_number}",
            notes=f"Worked {activation_log.activator.callsign} at bunker",
            created_by=created_by
        )
        
        # Update cached counts
        stats, _ = UserStatistics.objects.get_or_create(user=user)
        stats.total_hunter_qso += 1
        
        # Update unique bunkers hunted
        stats.unique_bunkers_hunted = ActivationLog.objects.filter(
            user=user
        ).exclude(activator=user).values('bunker').distinct().count()
        
        stats.save(update_fields=['total_hunter_qso', 'unique_bunkers_hunted'])
        
        logger.info(
            f"Awarded 1 hunter point to {user.callsign} "
            f"(ActivationLog {activation_log.id})"
        )
        
        return pts_transaction
    
    @staticmethod
    @transaction.atomic
    def confirm_b2b(log1, log2, created_by=None):
        """
        Confirm B2B connection and award points to both users.
        
        Args:
            log1: ActivationLog from user A
            log2: ActivationLog from user B (reciprocal)
            created_by: User or system that confirmed
            
        Returns:
            tuple: (transaction1, transaction2) or (None, None) if validation fails
        """
        # Validate that they're reciprocal (activator/user swapped)
        if log1.user != log2.activator or log2.user != log1.activator:
            logger.warning(
                f"Logs {log1.id} and {log2.id} are not reciprocal (users don't match)"
            )
            return None, None
        
        # Validate same bunker
        if log1.bunker != log2.bunker:
            logger.warning(
                f"Logs {log1.id} and {log2.id} have different bunkers"
            )
            return None, None
        
        # Check if already confirmed
        if log1.b2b_confirmed or log2.b2b_confirmed:
            logger.warning(
                f"B2B already confirmed for logs {log1.id} and {log2.id}"
            )
            return None, None
        
        # Mark logs as confirmed and link them
        now = timezone.now()
        
        log1.b2b_confirmed = True
        log1.b2b_confirmed_at = now
        log1.b2b_partner = log2.activator
        log1.b2b_partner_log = log2
        log1.save(update_fields=[
            'b2b_confirmed', 'b2b_confirmed_at', 'b2b_partner', 'b2b_partner_log'
        ])
        
        log2.b2b_confirmed = True
        log2.b2b_confirmed_at = now
        log2.b2b_partner = log1.activator
        log2.b2b_partner_log = log1
        log2.save(update_fields=[
            'b2b_confirmed', 'b2b_confirmed_at', 'b2b_partner', 'b2b_partner_log'
        ])
        
        # Award B2B points to both users
        tx1 = PointsTransaction.objects.create(
            user=log1.activator,
            transaction_type=PointsTransaction.B2B_CONFIRMED,
            b2b_points=1,  # 1 point per confirmed B2B
            activation_log=log1,
            bunker=log1.bunker,
            reason=f"B2B confirmed with {log2.activator.callsign}",
            notes=f"Bunkers: {log1.bunker.reference_number} ↔ {log2.bunker.reference_number}",
            created_by=created_by
        )
        
        tx2 = PointsTransaction.objects.create(
            user=log2.activator,
            transaction_type=PointsTransaction.B2B_CONFIRMED,
            b2b_points=1,
            activation_log=log2,
            bunker=log2.bunker,
            reason=f"B2B confirmed with {log1.activator.callsign}",
            notes=f"Bunkers: {log2.bunker.reference_number} ↔ {log1.bunker.reference_number}",
            created_by=created_by
        )
        
        # Update cached B2B counts
        for user in [log1.activator, log2.activator]:
            stats, _ = UserStatistics.objects.get_or_create(user=user)
            stats.total_b2b_qso = ActivationLog.objects.filter(
                activator=user,
                is_b2b=True,
                b2b_confirmed=True
            ).count()
            stats.save(update_fields=['total_b2b_qso'])
        
        logger.info(
            f"B2B confirmed: {log1.activator.callsign} ↔ {log2.activator.callsign} "
            f"(logs {log1.id}, {log2.id})"
        )
        
        return tx1, tx2
    
    @staticmethod
    @transaction.atomic
    def cancel_b2b(log, reason, created_by=None):
        """
        Cancel previously confirmed B2B (e.g., if log was deleted or invalid).
        
        Args:
            log: ActivationLog that was part of B2B
            reason: Why is it being cancelled
            created_by: User performing the action
            
        Returns:
            tuple: (reversal1, reversal2) or (None, None) if not confirmed
        """
        if not log.b2b_confirmed:
            return None, None
        
        partner_log = log.b2b_partner_log
        if not partner_log:
            logger.error(f"B2B confirmed but no partner log for {log.id}")
            return None, None
        
        # Find the B2B point transactions
        tx1 = PointsTransaction.objects.filter(
            user=log.activator,
            activation_log=log,
            transaction_type=PointsTransaction.B2B_CONFIRMED,
            is_reversed=False
        ).first()
        
        tx2 = PointsTransaction.objects.filter(
            user=partner_log.activator,
            activation_log=partner_log,
            transaction_type=PointsTransaction.B2B_CONFIRMED,
            is_reversed=False
        ).first()
        
        # Reverse the transactions
        reversal1 = tx1.reverse(reason=reason, created_by=created_by) if tx1 else None
        reversal2 = tx2.reverse(reason=reason, created_by=created_by) if tx2 else None
        
        # Unmark logs as confirmed
        log.b2b_confirmed = False
        log.b2b_confirmed_at = None
        log.save(update_fields=['b2b_confirmed', 'b2b_confirmed_at'])
        
        partner_log.b2b_confirmed = False
        partner_log.b2b_confirmed_at = None
        partner_log.save(update_fields=['b2b_confirmed', 'b2b_confirmed_at'])
        
        logger.info(f"B2B cancelled for logs {log.id} and {partner_log.id}: {reason}")
        
        return reversal1, reversal2
    
    @staticmethod
    @transaction.atomic
    def award_diploma_bonus(user, diploma, points=10, created_by=None):
        """
        Award bonus points for earning a diploma.
        
        Args:
            user: User who earned diploma
            diploma: Diploma instance
            points: How many bonus points (default 10)
            created_by: Who awarded this
            
        Returns:
            PointsTransaction instance
        """
        pts_transaction = PointsTransaction.objects.create(
            user=user,
            transaction_type=PointsTransaction.DIPLOMA_BONUS,
            diploma_points=points,
            diploma=diploma,
            reason=f"Earned diploma: {diploma.diploma_type.name_en}",
            notes=f"Diploma #{diploma.diploma_number}",
            created_by=created_by
        )
        
        logger.info(
            f"Awarded {points} diploma bonus points to {user.callsign} "
            f"for {diploma.diploma_type.name_en}"
        )
        
        return pts_transaction
    
    @staticmethod
    @transaction.atomic
    def create_batch(name, transactions, log_upload=None, created_by=None):
        """
        Group transactions into a batch for easier management.
        
        Args:
            name: Batch name
            transactions: List of PointsTransaction instances
            log_upload: Optional LogUpload this batch relates to
            created_by: Who created the batch
            
        Returns:
            PointsTransactionBatch instance
        """
        batch = PointsTransactionBatch.objects.create(
            name=name,
            description=f"Batch of {len(transactions)} transactions",
            log_upload=log_upload,
            created_by=created_by
        )
        
        batch.transactions.set(transactions)
        
        logger.info(f"Created transaction batch '{name}' with {len(transactions)} transactions")
        
        return batch
