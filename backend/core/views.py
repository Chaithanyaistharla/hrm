from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import User, EmployeeProfile
from .middleware import hr_or_admin_required, manager_or_above_required


@csrf_protect
@never_cache
def login_view(request):
    """Custom login view with role-based redirects."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                    
                    # Redirect to next page or dashboard
                    next_url = request.GET.get('next', 'dashboard')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Your account has been deactivated.')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Please provide both username and password.')
    
    return render(request, 'core/login.html')


def logout_view(request):
    """Logout view with message."""
    if request.user.is_authenticated:
        username = request.user.get_full_name() or request.user.username
        logout(request)
        messages.success(request, f'Goodbye, {username}! You have been logged out.')
    
    return redirect('login')


@login_required
def dashboard_view(request):
    """Dashboard view showing user info and role-based content."""
    user = request.user
    
    context = {
        'user': user,
        'role': user.role,
        'role_display': user.role_name if user.role else 'No Role Assigned',
        'is_hr': user.is_hr() if user.role else False,
        'is_manager': user.is_manager() if user.role else False,
        'is_admin_role': user.is_admin_role() if user.role else False,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
def profile_view(request):
    """User profile view."""
    return render(request, 'core/profile.html', {'user': request.user})


@login_required
def employee_profile_view(request):
    """Employee profile self-service view."""
    user = request.user
    
    # Get or create employee profile
    employee_profile, created = EmployeeProfile.objects.get_or_create(
        user=user,
        defaults={
            'designation': user.department or '',
            'date_of_joining': user.hire_date,
        }
    )
    
    if created:
        messages.info(request, 'Your employee profile has been created. Please complete your information.')
    
    context = {
        'user': user,
        'employee_profile': employee_profile,
    }
    
    return render(request, 'core/employee_profile.html', context)


@login_required
def employee_profile_edit_view(request):
    """Employee profile edit view for self-service."""
    user = request.user
    
    # Get or create employee profile
    employee_profile, created = EmployeeProfile.objects.get_or_create(
        user=user,
        defaults={
            'designation': user.department or '',
            'date_of_joining': user.hire_date,
        }
    )
    
    if request.method == 'POST':
        # Update basic user information
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.phone_number = request.POST.get('phone_number', '').strip()
        user.save()
        
        # Update employee profile
        employee_profile.personal_email = request.POST.get('personal_email', '').strip()
        employee_profile.date_of_birth = request.POST.get('date_of_birth') or None
        employee_profile.gender = request.POST.get('gender', '').strip()
        employee_profile.marital_status = request.POST.get('marital_status', '').strip()
        employee_profile.nationality = request.POST.get('nationality', '').strip()
        
        # Emergency contact
        employee_profile.emergency_contact_name = request.POST.get('emergency_contact_name', '').strip()
        employee_profile.emergency_contact_phone = request.POST.get('emergency_contact_phone', '').strip()
        employee_profile.emergency_contact_relationship = request.POST.get('emergency_contact_relationship', '').strip()
        
        # Address
        employee_profile.address_line_1 = request.POST.get('address_line_1', '').strip()
        employee_profile.address_line_2 = request.POST.get('address_line_2', '').strip()
        employee_profile.city = request.POST.get('city', '').strip()
        employee_profile.state = request.POST.get('state', '').strip()
        employee_profile.postal_code = request.POST.get('postal_code', '').strip()
        employee_profile.country = request.POST.get('country', '').strip()
        
        employee_profile.save()
        
        messages.success(request, 'Your profile has been updated successfully!')
        return redirect('employee_profile')
    
    context = {
        'user': user,
        'employee_profile': employee_profile,
    }
    
    return render(request, 'core/employee_profile_edit.html', context)


@login_required
@manager_or_above_required
def employee_directory_view(request):
    """Employee directory with search functionality."""
    search_query = request.GET.get('search', '').strip()
    department_filter = request.GET.get('department', '').strip()
    role_filter = request.GET.get('role', '').strip()
    
    # Base queryset - get all users with profiles
    employees = User.objects.select_related('role', 'employee_profile').filter(
        is_active=True
    ).order_by('last_name', 'first_name')
    
    # Apply search filter
    if search_query:
        employees = employees.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(department__icontains=search_query) |
            Q(employee_profile__designation__icontains=search_query)
        )
    
    # Apply department filter
    if department_filter:
        employees = employees.filter(department__icontains=department_filter)
    
    # Apply role filter
    if role_filter:
        employees = employees.filter(role__name=role_filter)
    
    # Get unique departments and roles for filters
    departments = User.objects.filter(is_active=True).exclude(
        department__isnull=True
    ).exclude(department__exact='').values_list(
        'department', flat=True
    ).distinct().order_by('department')
    
    roles = User.objects.filter(
        is_active=True, role__isnull=False
    ).select_related('role').values_list(
        'role__name', 'role__description'
    ).distinct().order_by('role__name')
    
    # Pagination
    paginator = Paginator(employees, 20)  # Show 20 employees per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'employees': page_obj,
        'search_query': search_query,
        'department_filter': department_filter,
        'role_filter': role_filter,
        'departments': departments,
        'roles': roles,
        'total_employees': employees.count(),
    }
    
    return render(request, 'core/employee_directory.html', context)


@login_required
@hr_or_admin_required
def employee_detail_view(request, user_id):
    """Detailed employee view for HR/Admin."""
    employee = get_object_or_404(User, id=user_id, is_active=True)
    
    # Get or create employee profile
    employee_profile, created = EmployeeProfile.objects.get_or_create(
        user=employee,
        defaults={
            'designation': employee.department or '',
            'date_of_joining': employee.hire_date,
        }
    )
    
    # Check if current user can manage this employee
    can_manage = employee_profile.can_be_managed_by(request.user)
    
    context = {
        'employee': employee,
        'employee_profile': employee_profile,
        'can_manage': can_manage,
    }
    
    return render(request, 'core/employee_detail.html', context)


@login_required
@manager_or_above_required
def employee_search_api(request):
    """API endpoint for employee search (AJAX)."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    employees = User.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(username__icontains=query) |
        Q(employee_id__icontains=query),
        is_active=True
    ).select_related('role')[:10]
    
    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'name': emp.get_full_name() or emp.username,
            'username': emp.username,
            'employee_id': emp.employee_id or '',
            'department': emp.department or '',
            'role': emp.role.get_name_display() if emp.role else 'No Role',
            'email': emp.email,
        })
    
    return JsonResponse({'results': results})
