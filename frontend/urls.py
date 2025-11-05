"""
Frontend URL configuration
"""
from django.urls import path
from . import views
from . import bunker_views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_log, name='upload_log'),
    path('diplomas/', views.diplomas_view, name='diplomas'),
    path('diplomas/<int:diploma_id>/download/', views.download_certificate, name='download_certificate'),
    path('verify-diploma/<str:diploma_number>/', views.verify_diploma_view, name='verify_diploma'),
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('cluster/', views.cluster_view, name='cluster'),
    
    # Legal pages
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('cookies/', views.cookie_policy, name='cookie_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    
    # Bunker views
    path('bunkers/', bunker_views.bunker_list, name='bunker_list'),
    path('bunkers/<path:reference>/', bunker_views.bunker_detail, name='bunker_detail'),
    path('bunkers-request/', bunker_views.request_bunker, name='request_bunker'),
    path('my-bunker-requests/', bunker_views.my_bunker_requests, name='my_bunker_requests'),
    
    # Staff/Admin only
    path('admin/bunker-requests/', bunker_views.manage_bunker_requests, name='manage_bunker_requests'),
    path('admin/bunker-requests/<int:request_id>/approve/', bunker_views.approve_bunker_request, name='approve_bunker_request'),
    path('admin/bunker-requests/<int:request_id>/reject/', bunker_views.reject_bunker_request, name='reject_bunker_request'),
    path('admin/upload-bunkers-csv/', bunker_views.upload_bunkers_csv, name='upload_bunkers_csv'),
]
