from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from .models import PlannedActivation
from .forms import PlannedActivationForm


@login_required
def planned_activation_list(request):
    """List all planned activations"""
    # Get filter parameters
    show_past = request.GET.get('show_past', 'no')
    search = request.GET.get('search', '')
    bunker_ref = request.GET.get('bunker', '')
    
    # Only staff and superuser can see past activations
    can_see_past = request.user.is_staff or request.user.is_superuser
    if not can_see_past:
        show_past = 'no'
    
    # Base queryset
    activations = PlannedActivation.objects.select_related('user', 'bunker').all()
    
    # Filter out past activations by default
    if show_past != 'yes':
        today = timezone.now().date()
        activations = activations.filter(planned_date__gte=today)
    
    # Filter by bunker reference if provided
    if bunker_ref:
        activations = activations.filter(bunker__reference_number=bunker_ref)
    
    # Search functionality
    if search:
        activations = activations.filter(
            Q(callsign__icontains=search) |
            Q(bunker__reference_number__icontains=search) |
            Q(bunker__name_pl__icontains=search) |
            Q(bunker__name_en__icontains=search) |
            Q(user__callsign__icontains=search) |
            Q(comments__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(activations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'show_past': show_past,
        'search': search,
        'bunker_ref': bunker_ref,
        'can_see_past': can_see_past,
    }
    return render(request, 'planned_activations/list.html', context)


@login_required
def planned_activation_detail(request, pk):
    """View details of a planned activation"""
    activation = get_object_or_404(
        PlannedActivation.objects.select_related('user', 'bunker'),
        pk=pk
    )
    
    context = {
        'activation': activation,
    }
    return render(request, 'planned_activations/detail.html', context)


@login_required
def planned_activation_create(request):
    """Create a new planned activation"""
    if request.method == 'POST':
        form = PlannedActivationForm(request.POST, user=request.user)
        if form.is_valid():
            activation = form.save(commit=False)
            activation.user = request.user
            activation.save()
            messages.success(request, _('Planned activation created successfully!'))
            return redirect('planned_activation_list')
    else:
        # Check if bunker reference is provided in URL
        bunker_ref = request.GET.get('bunker')
        initial_data = {}
        
        if bunker_ref:
            from bunkers.models import Bunker
            try:
                bunker = Bunker.objects.get(reference_number=bunker_ref)
                initial_data['bunker'] = bunker
            except Bunker.DoesNotExist:
                messages.warning(request, _('Bunker with reference %(ref)s not found.') % {'ref': bunker_ref})
        
        form = PlannedActivationForm(user=request.user, initial=initial_data)
    
    context = {
        'form': form,
        'action': 'create',
    }
    return render(request, 'planned_activations/form.html', context)


@login_required
def planned_activation_edit(request, pk):
    """Edit an existing planned activation"""
    activation = get_object_or_404(PlannedActivation, pk=pk)
    
    # Check permissions
    if not (request.user == activation.user or request.user.is_staff or request.user.is_superuser):
        messages.error(request, _('You do not have permission to edit this activation.'))
        return redirect('planned_activation_detail', pk=pk)
    
    if request.method == 'POST':
        form = PlannedActivationForm(request.POST, instance=activation, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _('Planned activation updated successfully!'))
            return redirect('planned_activation_detail', pk=pk)
    else:
        form = PlannedActivationForm(instance=activation, user=request.user)
    
    context = {
        'form': form,
        'activation': activation,
        'action': 'edit',
    }
    return render(request, 'planned_activations/form.html', context)


@login_required
def planned_activation_delete(request, pk):
    """Delete a planned activation"""
    activation = get_object_or_404(PlannedActivation, pk=pk)
    
    # Check permissions
    if not (request.user == activation.user or request.user.is_staff or request.user.is_superuser):
        messages.error(request, _('You do not have permission to delete this activation.'))
        return redirect('planned_activation_detail', pk=pk)
    
    if request.method == 'POST':
        activation.delete()
        messages.success(request, _('Planned activation deleted successfully!'))
        return redirect('planned_activation_list')
    
    context = {
        'activation': activation,
    }
    return render(request, 'planned_activations/delete_confirm.html', context)
