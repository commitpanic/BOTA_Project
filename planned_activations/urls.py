from django.urls import path
from . import views

urlpatterns = [
    path('', views.planned_activation_list, name='planned_activation_list'),
    path('create/', views.planned_activation_create, name='planned_activation_create'),
    path('<int:pk>/', views.planned_activation_detail, name='planned_activation_detail'),
    path('<int:pk>/edit/', views.planned_activation_edit, name='planned_activation_edit'),
    path('<int:pk>/delete/', views.planned_activation_delete, name='planned_activation_delete'),
]
