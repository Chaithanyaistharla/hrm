from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import date
import json
from .decorators import role_required, hr_required, admin_required
from .models import User, EmployeeProfile, Attendance
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
    """Role-based dashboard redirect view."""
    user = request.user
    
    # Redirect based on user role
    if user.is_hr() or user.is_admin_role():
        return redirect('dashboard_hr')
    else:
        # Default to employee dashboard for EMPLOYEE and MANAGER roles
        return redirect('dashboard_employee')


@login_required
def dashboard_employee_view(request):
    """Employee dashboard with attendance, leaves, and projects widgets."""
    user = request.user
    
    # Sample data for placeholders - will be replaced with real data later
    context = {
        'user': user,
        'role': user.role,
        'role_display': user.role_name if user.role else 'Employee',
        # Attendance widget data
        'attendance_data': {
            'today_status': 'Not Checked In',
            'this_week_hours': '32.5',
            'this_month_days': '18',
        },
        # Leave widget data
        'leave_data': {
            'pending_requests': 2,
            'available_days': 12,
            'upcoming_leaves': 'Dec 25-26, 2025',
        },
        # Project widget data
        'project_data': {
            'active_projects': 3,
            'tasks_due_today': 2,
            'recent_project': 'HRMS Development',
        },
    }
    
    return render(request, 'core/dashboard_employee.html', context)


@login_required
@hr_required
def dashboard_hr_view(request):
    """HR dashboard with organization-wide widgets and management tools."""
    user = request.user
    
    # Sample data for placeholders - will be replaced with real data later
    context = {
        'user': user,
        'role': user.role,
        'role_display': user.role_name if user.role else 'HR',
        # Organization overview widget data
        'org_data': {
            'total_employees': 45,
            'new_hires_this_month': 3,
            'active_employees': 42,
        },
        # Leave management widget data
        'leave_management': {
            'pending_approvals': 8,
            'approved_today': 2,
            'rejected_today': 1,
        },
        # Attendance overview widget data
        'attendance_overview': {
            'present_today': 38,
            'absent_today': 4,
            'late_arrivals': 2,
        },
        # Project management widget data
        'project_overview': {
            'active_projects': 12,
            'completed_this_month': 3,
            'overdue_projects': 1,
        },
    }
    
    return render(request, 'core/dashboard_hr.html', context)


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
    search_query = request.GET.get('q', '').strip()  # Use 'q' parameter as specified
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
            'role': emp.get_role_display() if emp.role else 'No Role',
            'email': emp.email,
        })
    
    return JsonResponse({'results': results})


# Test views for role-based access control
@hr_required
def hr_only_view(request):
    """Test view that only HR and Admin can access."""
    return render(request, 'core/test_view.html', {
        'title': 'HR Only Area',
        'message': 'This view is only accessible by HR and Admin users.',
        'user_role': request.user.role
    })


@admin_required
def admin_only_view(request):
    """Test view that only Admin can access."""
    return render(request, 'core/test_view.html', {
        'title': 'Admin Only Area', 
        'message': 'This view is only accessible by Admin users.',
        'user_role': request.user.role
    })


@login_required
def org_directory(request):
    """Organization directory with search by name/department/designation."""
    q = request.GET.get('q', '').strip()
    
    employees = User.objects.select_related('employeeprofile').filter(is_active=True)
    
    if q:
        employees = employees.filter(
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(employeeprofile__department__icontains=q) |
            Q(employeeprofile__designation__icontains=q)
        )
    
    employees = employees.order_by('last_name', 'first_name')
    
    return render(request, 'core/directory.html', {
        'employees': employees,
        'search_query': q,
    })


# ============================================================================
# ATTENDANCE API ENDPOINTS
# ============================================================================

@csrf_exempt
@require_POST
@login_required
def clock_in_api(request):
    """
    API endpoint for employee clock-in.
    Creates or updates today's attendance record with clock-in time.
    """
    try:
        # Get request metadata
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Get or create today's attendance record
        today = date.today()
        attendance, created = Attendance.objects.get_or_create(
            employee=request.user,
            date=today,
            defaults={
                'login_time': timezone.now(),
                'ip': ip_address,
                'device_info': user_agent,
            }
        )
        
        # If attendance already exists, update clock-in time if not already clocked in
        if not created:
            if attendance.login_time is None:
                attendance.login_time = timezone.now()
                attendance.ip = ip_address
                attendance.device_info = user_agent
                attendance.save()
                message = "Clock-in successful"
                status = "success"
            else:
                message = f"Already clocked in today at {attendance.login_time.strftime('%H:%M:%S')}"
                status = "warning"
        else:
            message = "Clock-in successful"
            status = "success"
        
        return JsonResponse({
            'status': status,
            'message': message,
            'data': {
                'employee': request.user.get_full_name() or request.user.username,
                'date': today.isoformat(),
                'clock_in_time': attendance.login_time.isoformat() if attendance.login_time else None,
                'ip_address': attendance.ip,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Clock-in failed: {str(e)}',
            'data': None
        }, status=500)


@csrf_exempt
@require_POST
@login_required
def clock_out_api(request):
    """
    API endpoint for employee clock-out.
    Updates today's attendance record with clock-out time.
    """
    try:
        # Get request metadata
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Get today's attendance record
        today = date.today()
        try:
            attendance = Attendance.objects.get(
                employee=request.user,
                date=today
            )
        except Attendance.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'No clock-in record found for today. Please clock-in first.',
                'data': None
            }, status=400)
        
        # Check if already clocked out
        if attendance.logout_time is not None:
            return JsonResponse({
                'status': 'warning',
                'message': f'Already clocked out today at {attendance.logout_time.strftime("%H:%M:%S")}',
                'data': {
                    'employee': request.user.get_full_name() or request.user.username,
                    'date': today.isoformat(),
                    'clock_in_time': attendance.login_time.isoformat() if attendance.login_time else None,
                    'clock_out_time': attendance.logout_time.isoformat(),
                    'ip_address': attendance.ip,
                }
            })
        
        # Check if user has clocked in
        if attendance.login_time is None:
            return JsonResponse({
                'status': 'error',
                'message': 'Cannot clock out without clocking in first.',
                'data': None
            }, status=400)
        
        # Update clock-out time
        attendance.logout_time = timezone.now()
        # Update IP and device info for clock-out (in case of different device/location)
        if ip_address and ip_address != attendance.ip:
            attendance.device_info += f" | Clock-out: {user_agent}"
        attendance.save()
        
        # Calculate working hours
        working_duration = attendance.logout_time - attendance.login_time
        working_hours = working_duration.total_seconds() / 3600
        
        return JsonResponse({
            'status': 'success',
            'message': 'Clock-out successful',
            'data': {
                'employee': request.user.get_full_name() or request.user.username,
                'date': today.isoformat(),
                'clock_in_time': attendance.login_time.isoformat(),
                'clock_out_time': attendance.logout_time.isoformat(),
                'working_hours': round(working_hours, 2),
                'ip_address': attendance.ip,
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Clock-out failed: {str(e)}',
            'data': None
        }, status=500)


@login_required
def attendance_status_api(request):
    """
    API endpoint to get current attendance status for the user.
    """
    try:
        today = date.today()
        try:
            attendance = Attendance.objects.get(
                employee=request.user,
                date=today
            )
            
            status_data = {
                'employee': request.user.get_full_name() or request.user.username,
                'date': today.isoformat(),
                'clock_in_time': attendance.login_time.isoformat() if attendance.login_time else None,
                'clock_out_time': attendance.logout_time.isoformat() if attendance.logout_time else None,
                'ip_address': attendance.ip,
                'is_clocked_in': attendance.login_time is not None,
                'is_clocked_out': attendance.logout_time is not None,
            }
            
            if attendance.login_time and attendance.logout_time:
                working_duration = attendance.logout_time - attendance.login_time
                status_data['working_hours'] = round(working_duration.total_seconds() / 3600, 2)
            elif attendance.login_time:
                current_duration = timezone.now() - attendance.login_time
                status_data['current_working_hours'] = round(current_duration.total_seconds() / 3600, 2)
            
        except Attendance.DoesNotExist:
            status_data = {
                'employee': request.user.get_full_name() or request.user.username,
                'date': today.isoformat(),
                'clock_in_time': None,
                'clock_out_time': None,
                'ip_address': None,
                'is_clocked_in': False,
                'is_clocked_out': False,
            }
        
        return JsonResponse({
            'status': 'success',
            'message': 'Attendance status retrieved successfully',
            'data': status_data
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to retrieve attendance status: {str(e)}',
            'data': None
        }, status=500)


@login_required
def attendance_page(request):
    """
    Attendance management page for employees.
    """
    return render(request, 'core/attendance.html')


@login_required
def employee_attendance_dashboard(request):
    """
    Employee attendance dashboard showing today's times and weekly summary.
    """
    from datetime import datetime, timedelta
    
    user = request.user
    today = date.today()
    
    # Get today's attendance
    today_attendance = Attendance.objects.filter(
        employee=user,
        date=today
    ).first()
    
    # Get last 7 days attendance for weekly summary
    seven_days_ago = today - timedelta(days=6)
    weekly_attendance = Attendance.objects.filter(
        employee=user,
        date__range=[seven_days_ago, today]
    ).order_by('-date')
    
    # Calculate total hours for the week
    total_weekly_hours = sum(
        record.working_hours or 0 
        for record in weekly_attendance
    )
    
    context = {
        'today_attendance': today_attendance,
        'weekly_attendance': weekly_attendance,
        'total_weekly_hours': round(total_weekly_hours, 2),
        'today': today,
    }
    
    return render(request, 'core/employee_attendance_dashboard.html', context)


@login_required
@manager_or_above_required
def team_attendance_view(request):
    """
    Manager/HR team attendance view with filters for date range and department.
    """
    from datetime import datetime, timedelta
    from django.db.models import Q
    
    # Get filter parameters from query params
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    department = request.GET.get('department', '')
    employee_name = request.GET.get('employee_name', '')
    
    # Default to current week if no dates provided
    if not date_from or not date_to:
        today = date.today()
        # Start of current week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        date_from = start_of_week.strftime('%Y-%m-%d')
        date_to = today.strftime('%Y-%m-%d')
    
    # Convert string dates to date objects
    try:
        from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
        to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        from_date = date.today()
        to_date = date.today()
    
    # Build query for attendance records
    attendance_query = Q(date__range=[from_date, to_date])
    
    # Filter by department if specified
    if department:
        attendance_query &= Q(employee__department__icontains=department)
    
    # Filter by employee name if specified
    if employee_name:
        attendance_query &= Q(
            Q(employee__first_name__icontains=employee_name) |
            Q(employee__last_name__icontains=employee_name) |
            Q(employee__username__icontains=employee_name)
        )
    
    # Get attendance records
    attendance_records = Attendance.objects.filter(
        attendance_query
    ).select_related('employee').order_by('-date', 'employee__first_name')
    
    # Get unique departments for filter dropdown
    departments = User.objects.exclude(
        department__isnull=True
    ).exclude(
        department=''
    ).values_list('department', flat=True).distinct().order_by('department')
    
    # Pagination
    paginator = Paginator(attendance_records, 20)  # 20 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'attendance_records': page_obj,
        'departments': departments,
        'date_from': date_from,
        'date_to': date_to,
        'department': department,
        'employee_name': employee_name,
        'total_records': attendance_records.count(),
    }
    
    return render(request, 'core/team_attendance_view.html', context)
