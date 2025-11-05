"""
Custom Admin Site with enhanced dashboard
"""
from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Count
from accounts.models import User
from bunkers.models import Bunker
from activations.models import ActivationLog
from diplomas.models import Diploma
from cluster.models import Spot


class BOTAAdminSite(admin.AdminSite):
    site_header = "Administracja SPBOTA App"
    site_title = "SPBOTA Admin"
    index_title = "Panel Administracyjny SPBOTA"
    
    def index(self, request, extra_context=None):
        """
        Custom admin index with statistics
        """
        extra_context = extra_context or {}
        
        # Get statistics
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'auto_created_users': User.objects.filter(auto_created=True, is_active=False).count(),
            'staff_users': User.objects.filter(is_staff=True).count(),
            'superusers': User.objects.filter(is_superuser=True).count(),
            
            'total_bunkers': Bunker.objects.count(),
            'verified_bunkers': Bunker.objects.filter(is_verified=True).count(),
            'pending_bunkers': Bunker.objects.filter(is_verified=False).count(),
            
            'total_qsos': ActivationLog.objects.count(),
            'verified_qsos': ActivationLog.objects.filter(verified=True).count(),
            'b2b_qsos': ActivationLog.objects.filter(is_b2b=True).count(),
            
            'total_diplomas': Diploma.objects.count(),
            'active_spots': Spot.objects.filter(is_active=True).count(),
        }
        
        # Recent activity
        recent_users = User.objects.order_by('-date_joined')[:5]
        recent_activations = ActivationLog.objects.select_related('user', 'bunker').order_by('-activation_date')[:10]
        recent_diplomas = Diploma.objects.select_related('user', 'diploma_type').order_by('-issue_date')[:5]
        
        extra_context.update({
            'stats': stats,
            'recent_users': recent_users,
            'recent_activations': recent_activations,
            'recent_diplomas': recent_diplomas,
        })
        
        return super().index(request, extra_context)


# Create custom admin site instance
bota_admin_site = BOTAAdminSite(name='bota_admin')
