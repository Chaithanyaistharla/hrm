from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from django.db.models import Q, Sum
from django.db import models
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from datetime import date
import json
from .decorators import role_required, hr_required, admin_required, manager_or_hr_required, can_manage_leave
from .models import User, EmployeeProfile, Attendance, Leave, Project, ProjectMember, TimesheetEntry, Payslip
from .middleware import hr_or_admin_required, manager_or_above_required
from .forms import LeaveApplicationForm, ProjectForm, ProjectMemberForm, ProjectMemberEditForm, TimesheetEntryForm, TimesheetEntryEditForm, PayslipForm, PayslipBulkUploadForm


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
    from datetime import date, timedelta, datetime
    from django.utils import timezone
    from django.db.models import Sum, Count
    
    today = date.today()
    this_week_start = today - timedelta(days=today.weekday())
    this_week_end = this_week_start + timedelta(days=6)
    this_month_start = today.replace(day=1)
    
    # Get today's attendance status
    today_attendance = Attendance.objects.filter(employee=user, date=today).first()
    today_status = 'Not Checked In'
    if today_attendance:
        if today_attendance.is_clocked_in:
            today_status = f'Checked In at {today_attendance.login_time.strftime("%H:%M")}'
        else:
            today_status = f'Completed ({today_attendance.working_hours}h)'
    
    # Get weekly worked hours from timesheets
    weekly_timesheet_hours = TimesheetEntry.objects.filter(
        employee=user,
        date__range=[this_week_start, this_week_end]
    ).aggregate(total=Sum('hours'))['total'] or 0
    
    # Get monthly attendance days
    monthly_attendance_days = Attendance.objects.filter(
        employee=user,
        date__gte=this_month_start
    ).count()
    
    # Get leave data
    pending_leaves = Leave.objects.filter(employee=user, status='PENDING').count()
    approved_leaves_this_year = Leave.objects.filter(
        employee=user,
        status='APPROVED',
        from_date__year=today.year
    )
    used_leave_days = sum(leave.duration_days for leave in approved_leaves_this_year)
    available_leave_days = 25 - used_leave_days  # Assuming 25 annual leave days
    
    # Get upcoming approved leaves
    upcoming_leaves = Leave.objects.filter(
        employee=user,
        status='APPROVED',
        from_date__gte=today
    ).order_by('from_date')[:3]
    upcoming_leaves_text = ', '.join([
        f"{leave.from_date.strftime('%b %d')}{('-' + leave.to_date.strftime('%d')) if leave.from_date != leave.to_date else ''}"
        for leave in upcoming_leaves
    ]) or 'No upcoming leaves'
    
    # Get project data
    active_projects = ProjectMember.objects.filter(
        employee=user,
        project__status='ACTIVE'
    ).count()
    
    # Get recent project
    recent_project_member = ProjectMember.objects.filter(
        employee=user,
        project__status='ACTIVE'
    ).select_related('project').order_by('-joined_on').first()
    recent_project_name = recent_project_member.project.name if recent_project_member else 'No active projects'
    
    # Get today's timesheet entries count as "tasks"
    today_timesheet_entries = TimesheetEntry.objects.filter(
        employee=user,
        date=today
    ).count()
    
    context = {
        'user': user,
        'role': user.role,
        'role_display': user.get_role_display() if user.role else 'Employee',
        # Attendance widget data
        'attendance_data': {
            'today_status': today_status,
            'this_week_hours': f'{weekly_timesheet_hours}',
            'this_month_days': str(monthly_attendance_days),
        },
        # Leave widget data
        'leave_data': {
            'pending_requests': pending_leaves,
            'available_days': max(0, available_leave_days),
            'upcoming_leaves': upcoming_leaves_text,
        },
        # Project widget data
        'project_data': {
            'active_projects': active_projects,
            'tasks_due_today': today_timesheet_entries,
            'recent_project': recent_project_name,
        },
    }
    
    return render(request, 'core/dashboard_employee.html', context)


@login_required
@hr_required
def dashboard_hr_view(request):
    """HR dashboard with organization-wide widgets and management tools."""
    user = request.user
    from datetime import date, timedelta, datetime
    from django.utils import timezone
    from django.db.models import Sum, Count
    
    today = date.today()
    this_month_start = today.replace(day=1)
    
    # Organization overview data
    total_employees = User.objects.filter(is_active=True).count()
    new_hires_this_month = User.objects.filter(
        hire_date__gte=this_month_start,
        is_active=True
    ).count()
    active_employees = User.objects.filter(
        is_active=True
    ).count()
    
    # Leave management data
    pending_leaves = Leave.objects.filter(status='PENDING').count()
    approved_today = Leave.objects.filter(
        approved_on__date=today,
        status='APPROVED'
    ).count()
    rejected_today = Leave.objects.filter(
        updated_at__date=today,
        status='REJECTED'
    ).count()
    
    # Attendance overview data
    today_attendance = Attendance.objects.filter(date=today)
    present_today = today_attendance.count()
    total_active_employees = User.objects.filter(is_active=True).count()
    absent_today = max(0, total_active_employees - present_today)
    
    # Late arrivals (assuming work starts at 9:00 AM)
    from datetime import time
    work_start_time = time(9, 0)
    late_arrivals = today_attendance.filter(
        login_time__time__gt=work_start_time
    ).count()
    
    # Project overview data
    active_projects = Project.objects.filter(status='ACTIVE').count()
    completed_this_month = Project.objects.filter(
        status='COMPLETED',
        updated_at__gte=this_month_start
    ).count()
    
    # Overdue projects (projects with end_date in the past but still active)
    overdue_projects = Project.objects.filter(
        status='ACTIVE',
        end_date__lt=today
    ).count()
    
    context = {
        'user': user,
        'role': user.role,
        'role_display': user.get_role_display() if user.role else 'HR',
        # Organization overview widget data
        'org_data': {
            'total_employees': total_employees,
            'new_hires_this_month': new_hires_this_month,
            'active_employees': active_employees,
        },
        # Leave management widget data
        'leave_management': {
            'pending_approvals': pending_leaves,
            'approved_today': approved_today,
            'rejected_today': rejected_today,
        },
        # Attendance overview widget data
        'attendance_overview': {
            'present_today': present_today,
            'absent_today': absent_today,
            'late_arrivals': late_arrivals,
        },
        # Project management widget data
        'project_overview': {
            'active_projects': active_projects,
            'completed_this_month': completed_this_month,
            'overdue_projects': overdue_projects,
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


@login_required
def apply_leave(request):
    """
    View for employees to apply for leave.
    """
    user_profile = None
    if hasattr(request.user, 'employeeprofile'):
        user_profile = request.user.employeeprofile
    
    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = request.user
            leave.status = 'PENDING'
            leave.save()
            
            messages.success(
                request,
                f'Your {leave.get_leave_type_display().lower()} application from '
                f'{leave.from_date} to {leave.to_date} has been submitted successfully '
                f'and is pending approval.'
            )
            return redirect('my_leaves')
    else:
        form = LeaveApplicationForm(user=request.user)
    
    # Get leave balances
    leave_balances = {}
    if user_profile:
        leave_balances = {
            'Annual Leave': user_profile.annual_leaves,
            'Sick Leave': user_profile.sick_leaves,
            'Maternity Leave': user_profile.maternity_leaves,
            'Paternity Leave': user_profile.paternity_leaves,
            'Emergency Leave': user_profile.emergency_leaves,
            'Compensatory Leave': user_profile.compensatory_leaves,
        }
    
    context = {
        'form': form,
        'leave_balances': leave_balances,
        'user_profile': user_profile,
    }
    
    return render(request, 'core/apply_leave.html', context)


@login_required
def my_leaves(request):
    """
    View for employees to see their leave history and status.
    """
    # Get all leaves for the current user
    leaves = Leave.objects.filter(
        employee=request.user
    ).order_by('-applied_on')
    
    # Pagination
    paginator = Paginator(leaves, 10)  # 10 leaves per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get leave balances
    user_profile = None
    leave_balances = {}
    current_year_usage = {}
    
    if hasattr(request.user, 'employeeprofile'):
        user_profile = request.user.employeeprofile
        leave_balances = {
            'ANNUAL': user_profile.annual_leaves,
            'SICK': user_profile.sick_leaves,
            'MATERNITY': user_profile.maternity_leaves,
            'PATERNITY': user_profile.paternity_leaves,
            'EMERGENCY': user_profile.emergency_leaves,
            'COMPENSATORY': user_profile.compensatory_leaves,
        }
        
        # Calculate current year usage
        from datetime import datetime
        current_year = datetime.now().year
        
        for leave_type in leave_balances.keys():
            used_days = Leave.objects.filter(
                employee=request.user,
                leave_type=leave_type,
                status='APPROVED',
                from_date__year=current_year
            ).aggregate(
                total=models.Sum('duration_days')
            )['total'] or 0
            
            current_year_usage[leave_type] = {
                'used': used_days,
                'available': max(0, leave_balances[leave_type] - used_days),
                'total': leave_balances[leave_type]
            }
    
    context = {
        'leaves': page_obj,
        'leave_balances': leave_balances,
        'current_year_usage': current_year_usage,
        'user_profile': user_profile,
    }
    
    return render(request, 'core/my_leaves.html', context)


@login_required
@manager_or_hr_required
def manager_pending_leaves(request):
    """
    View for managers to see and approve/reject pending leaves of their direct reports.
    """
    user = request.user
    
    # Get filter parameters
    leave_type_filter = request.GET.get('leave_type', '')
    employee_filter = request.GET.get('employee', '')
    
    # Build base query - managers only see their direct reports
    if user.is_manager() and not user.is_hr() and not user.is_admin_role():
        # Get direct reports only
        direct_reports = User.objects.filter(employeeprofile__manager=user)
        leave_query = Q(employee__in=direct_reports, status='PENDING')
    else:
        # HR and Admin can see all pending leaves
        leave_query = Q(status='PENDING')
    
    # Apply filters
    if leave_type_filter:
        leave_query &= Q(leave_type=leave_type_filter)
    
    if employee_filter:
        leave_query &= Q(
            Q(employee__first_name__icontains=employee_filter) |
            Q(employee__last_name__icontains=employee_filter) |
            Q(employee__username__icontains=employee_filter)
        )
    
    # Get pending leave requests
    pending_leaves = Leave.objects.filter(
        leave_query
    ).select_related(
        'employee', 
        'employee__employeeprofile'
    ).order_by('-applied_on')
    
    # Pagination
    paginator = Paginator(pending_leaves, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get direct reports for filter (managers only)
    direct_reports = []
    if user.is_manager():
        direct_reports = User.objects.filter(
            employeeprofile__manager=user
        ).values_list('id', 'first_name', 'last_name')
    
    context = {
        'pending_leaves': page_obj,
        'leave_type_filter': leave_type_filter,
        'employee_filter': employee_filter,
        'leave_types': Leave.LEAVE_TYPE_CHOICES,
        'direct_reports': direct_reports,
        'is_manager_view': user.is_manager() and not user.is_hr() and not user.is_admin_role(),
        'pending_count': pending_leaves.count(),
    }
    
    return render(request, 'core/manager_pending_leaves.html', context)


@login_required
@hr_required
def hr_all_leaves(request):
    """
    HR view to see all leave requests with comprehensive filters.
    """
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    employee_filter = request.GET.get('employee', '')
    leave_type_filter = request.GET.get('leave_type', '')
    department_filter = request.GET.get('department', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Build query
    leave_query = Q()
    
    if status_filter:
        leave_query &= Q(status=status_filter)
    
    if employee_filter:
        leave_query &= Q(
            Q(employee__first_name__icontains=employee_filter) |
            Q(employee__last_name__icontains=employee_filter) |
            Q(employee__username__icontains=employee_filter) |
            Q(employee__employee_id__icontains=employee_filter)
        )
    
    if leave_type_filter:
        leave_query &= Q(leave_type=leave_type_filter)
    
    if department_filter:
        leave_query &= Q(employee__department__icontains=department_filter)
    
    if date_from:
        leave_query &= Q(from_date__gte=date_from)
        
    if date_to:
        leave_query &= Q(to_date__lte=date_to)
    
    # Get all leave requests
    all_leaves = Leave.objects.filter(
        leave_query
    ).select_related(
        'employee',
        'employee__employeeprofile', 
        'approver'
    ).order_by('-applied_on')
    
    # Pagination
    paginator = Paginator(all_leaves, 20)  # 20 requests per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique departments for filter
    departments = User.objects.values_list(
        'department', flat=True
    ).distinct().exclude(department='').order_by('department')
    
    # Get leave statistics
    leave_stats = {
        'total': all_leaves.count(),
        'pending': all_leaves.filter(status='PENDING').count(),
        'approved': all_leaves.filter(status='APPROVED').count(),
        'rejected': all_leaves.filter(status='REJECTED').count(),
    }
    
    context = {
        'all_leaves': page_obj,
        'status_filter': status_filter,
        'employee_filter': employee_filter,
        'leave_type_filter': leave_type_filter,
        'department_filter': department_filter,
        'date_from': date_from,
        'date_to': date_to,
        'leave_types': Leave.LEAVE_TYPE_CHOICES,
        'statuses': Leave.STATUS_CHOICES,
        'departments': departments,
        'leave_stats': leave_stats,
    }
    
    return render(request, 'core/hr_all_leaves.html', context)


@login_required
@manager_or_above_required
def manage_team_leaves(request):
    """
    Legacy view - redirects to appropriate view based on user role.
    """
    user = request.user
    
    if user.is_hr() or user.is_admin_role():
        return redirect('hr_all_leaves')
    elif user.is_manager():
        return redirect('manager_pending_leaves')
    else:
        messages.error(request, 'You do not have permission to manage leaves.')
        return redirect('dashboard')


@login_required
@manager_or_hr_required
@require_POST
def approve_leave(request, leave_id):
    """
    Approve a leave request with balance deduction.
    """
    leave = get_object_or_404(Leave, id=leave_id)
    
    # Check if user can manage this leave
    if not can_manage_leave(request.user, leave):
        messages.error(request, 'You do not have permission to manage this leave request.')
        return redirect('dashboard')
    
    if leave.status != 'PENDING':
        messages.error(request, 'This leave request has already been processed.')
    else:
        # Check if employee has sufficient balance
        try:
            employee_profile = leave.employee.employeeprofile
            duration = leave.duration_days
            
            # Get current balance
            balance_field_map = {
                'ANNUAL': 'annual_leaves',
                'SICK': 'sick_leaves',
                'MATERNITY': 'maternity_leaves',
                'PATERNITY': 'paternity_leaves',
                'EMERGENCY': 'emergency_leaves',
                'COMPENSATORY': 'compensatory_leaves',
            }
            
            if leave.leave_type in balance_field_map:
                balance_field = balance_field_map[leave.leave_type]
                current_balance = getattr(employee_profile, balance_field)
                
                if current_balance >= duration:
                    # Deduct from balance
                    setattr(employee_profile, balance_field, current_balance - duration)
                    employee_profile.save()
                    
                    # Approve the leave
                    leave.status = 'APPROVED'
                    leave.approver = request.user
                    leave.approved_on = timezone.now()
                    leave.save()
                    
                    messages.success(
                        request,
                        f'{leave.employee.get_full_name()}\'s {leave.get_leave_type_display().lower()} '
                        f'from {leave.from_date} to {leave.to_date} has been approved. '
                        f'{duration} days deducted from {leave.get_leave_type_display().lower()} balance.'
                    )
                else:
                    messages.error(
                        request,
                        f'Cannot approve leave. {leave.employee.get_full_name()} has insufficient '
                        f'{leave.get_leave_type_display().lower()} balance. '
                        f'Required: {duration} days, Available: {current_balance} days.'
                    )
            else:
                # For leave types without balance tracking (like UNPAID, OTHER)
                leave.status = 'APPROVED'
                leave.approver = request.user
                leave.approved_on = timezone.now()
                leave.save()
                
                messages.success(
                    request,
                    f'{leave.employee.get_full_name()}\'s {leave.get_leave_type_display().lower()} '
                    f'from {leave.from_date} to {leave.to_date} has been approved.'
                )
                
        except EmployeeProfile.DoesNotExist:
            messages.error(
                request,
                f'Cannot approve leave. Employee profile not found for {leave.employee.get_full_name()}.'
            )
    
    # Redirect based on user role
    if request.user.is_hr() or request.user.is_admin_role():
        return redirect('hr_all_leaves')
    else:
        return redirect('manager_pending_leaves')


@login_required
@manager_or_hr_required
@require_POST
def reject_leave(request, leave_id):
    """
    Reject a leave request with optional reason.
    """
    leave = get_object_or_404(Leave, id=leave_id)
    
    # Check if user can manage this leave
    if not can_manage_leave(request.user, leave):
        messages.error(request, 'You do not have permission to manage this leave request.')
        return redirect('dashboard')
    
    if leave.status != 'PENDING':
        messages.error(request, 'This leave request has already been processed.')
    else:
        # Get rejection reason from form data
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        
        leave.status = 'REJECTED'
        leave.approver = request.user
        leave.approved_on = timezone.now()
        leave.rejection_reason = rejection_reason
        leave.save()
        
        reason_text = f' Reason: {rejection_reason}' if rejection_reason else ''
        
        messages.warning(
            request,
            f'{leave.employee.get_full_name()}\'s {leave.get_leave_type_display().lower()} '
            f'from {leave.from_date} to {leave.to_date} has been rejected.{reason_text}'
        )
    
    # Redirect based on user role
    if request.user.is_hr() or request.user.is_admin_role():
        return redirect('hr_all_leaves')
    else:
        return redirect('manager_pending_leaves')


# ============================
# PROJECT MANAGEMENT VIEWS
# ============================

@login_required
@hr_required
def project_list(request):
    """
    View for HR/Admin to list all projects with search and filter capabilities.
    """
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    manager_filter = request.GET.get('manager', '')
    
    # Build query
    projects = Project.objects.all()
    
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    if manager_filter:
        projects = projects.filter(manager_id=manager_filter)
    
    # Order by most recent
    projects = projects.select_related('manager').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(projects, 12)  # 12 projects per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get managers for filter
    managers = User.objects.filter(
        role__in=['MANAGER', 'HR', 'ADMIN']
    ).order_by('first_name', 'last_name')
    
    context = {
        'projects': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'manager_filter': manager_filter,
        'managers': managers,
        'status_choices': Project.STATUS_CHOICES,
        'total_projects': projects.count(),
    }
    
    return render(request, 'core/project_list.html', context)


@login_required
@hr_required
def project_create(request):
    """
    View for HR/Admin to create new projects.
    """
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            messages.success(
                request, 
                f'Project "{project.name}" has been created successfully.'
            )
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    
    context = {
        'form': form,
        'action': 'Create',
    }
    
    return render(request, 'core/project_form.html', context)


@login_required
@hr_required
def project_edit(request, project_id):
    """
    View for HR/Admin to edit existing projects.
    """
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save()
            messages.success(
                request, 
                f'Project "{project.name}" has been updated successfully.'
            )
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'form': form,
        'project': project,
        'action': 'Edit',
    }
    
    return render(request, 'core/project_form.html', context)


@login_required
def project_detail(request, project_id):
    """
    View for displaying project details and team members.
    Accessible by HR/Admin and project members.
    """
    project = get_object_or_404(Project, id=project_id)
    
    # Check permission
    user_can_manage = request.user.is_hr() or request.user.is_admin_role()
    is_project_member = ProjectMember.objects.filter(
        project=project, employee=request.user
    ).exists()
    is_project_manager = project.manager == request.user
    
    if not (user_can_manage or is_project_member or is_project_manager):
        messages.error(request, 'You do not have permission to view this project.')
        return redirect('my_projects')
    
    # Get project members
    members = ProjectMember.objects.filter(
        project=project
    ).select_related('employee', 'employee__employeeprofile').order_by('joined_on')
    
    # Forms for adding members (only for HR/Admin)
    add_member_form = None
    if user_can_manage:
        add_member_form = ProjectMemberForm(project=project)
    
    context = {
        'project': project,
        'members': members,
        'add_member_form': add_member_form,
        'user_can_manage': user_can_manage,
        'is_project_member': is_project_member,
        'is_project_manager': is_project_manager,
        'member_count': members.count(),
    }
    
    return render(request, 'core/project_detail.html', context)


@login_required
@hr_required
def project_delete(request, project_id):
    """
    View for HR/Admin to delete projects.
    """
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(
            request, 
            f'Project "{project_name}" has been deleted successfully.'
        )
        return redirect('project_list')
    
    context = {
        'project': project,
        'member_count': project.projectmember_set.count(),
    }
    
    return render(request, 'core/project_delete_confirm.html', context)


@login_required
@hr_required
@require_POST
def project_add_member(request, project_id):
    """
    View for HR/Admin to add members to projects.
    """
    project = get_object_or_404(Project, id=project_id)
    form = ProjectMemberForm(request.POST, project=project)
    
    if form.is_valid():
        member = form.save(commit=False)
        member.project = project
        member.save()
        
        messages.success(
            request,
            f'{member.employee.get_full_name()} has been added to "{project.name}" '
            f'as {member.role or "team member"}.'
        )
    else:
        for error in form.non_field_errors():
            messages.error(request, error)
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(request, f'{field}: {error}')
    
    return redirect('project_detail', project_id=project.id)


@login_required
@hr_required
def project_edit_member(request, project_id, member_id):
    """
    View for HR/Admin to edit project member roles.
    """
    project = get_object_or_404(Project, id=project_id)
    member = get_object_or_404(ProjectMember, id=member_id, project=project)
    
    if request.method == 'POST':
        form = ProjectMemberEditForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'{member.employee.get_full_name()}\'s role has been updated to '
                f'"{member.role or "team member"}".'
            )
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectMemberEditForm(instance=member)
    
    context = {
        'form': form,
        'project': project,
        'member': member,
    }
    
    return render(request, 'core/project_member_edit.html', context)


@login_required
@hr_required
@require_POST
def project_remove_member(request, project_id, member_id):
    """
    View for HR/Admin to remove members from projects.
    """
    project = get_object_or_404(Project, id=project_id)
    member = get_object_or_404(ProjectMember, id=member_id, project=project)
    
    employee_name = member.employee.get_full_name()
    member.delete()
    
    messages.success(
        request,
        f'{employee_name} has been removed from "{project.name}".'
    )
    
    return redirect('project_detail', project_id=project.id)


@login_required
def my_projects(request):
    """
    View for employees to see their current projects and team members.
    """
    # Get projects where user is a member
    member_projects = Project.objects.filter(
        projectmember__employee=request.user
    ).select_related('manager').order_by('name')
    
    # Get projects where user is the manager
    managed_projects = Project.objects.filter(
        manager=request.user
    ).select_related('manager').order_by('name')
    
    # Get project memberships with details
    memberships = ProjectMember.objects.filter(
        employee=request.user
    ).select_related('project', 'project__manager').order_by('project__name')
    
    # Create a list of projects with membership details
    project_details = []
    
    # Add projects where user is a member
    for membership in memberships:
        team_members = ProjectMember.objects.filter(
            project=membership.project
        ).select_related('employee', 'employee__employeeprofile').order_by('employee__first_name')
        
        project_details.append({
            'project': membership.project,
            'my_role': membership.role,
            'team_members': team_members,
            'is_manager': False,
        })
    
    # Add projects where user is manager but not a member
    for project in managed_projects:
        if not project.projectmember_set.filter(employee=request.user).exists():
            team_members = ProjectMember.objects.filter(
                project=project
            ).select_related('employee', 'employee__employeeprofile').order_by('employee__first_name')
            
            project_details.append({
                'project': project,
                'my_role': 'Project Manager',
                'team_members': team_members,
                'is_manager': True,
            })
    
    context = {
        'project_details': project_details,
        'total_projects': len(project_details),
    }
    
    return render(request, 'core/my_projects.html', context)


# ============================
# TIMESHEET MANAGEMENT VIEWS
# ============================

@login_required
def timesheet_entry(request):
    """
    View for employees to submit daily timesheet entries.
    """
    if request.method == 'POST':
        form = TimesheetEntryForm(request.POST, user=request.user)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.employee = request.user
            entry.save()
            
            messages.success(
                request,
                f'Timesheet entry for {entry.date} has been submitted successfully. '
                f'Hours: {entry.hours}, Project: {entry.project.name if entry.project else "No Project"}'
            )
            return redirect('timesheet_weekly_summary')
    else:
        form = TimesheetEntryForm(user=request.user)
    
    # Get recent entries for context
    recent_entries = TimesheetEntry.objects.filter(
        employee=request.user
    ).select_related('project').order_by('-date', '-created_at')[:5]
    
    # Get today's total hours
    from django.db.models import Sum
    today_total = TimesheetEntry.objects.filter(
        employee=request.user,
        date=date.today()
    ).aggregate(total=Sum('hours'))['total'] or 0
    
    context = {
        'form': form,
        'recent_entries': recent_entries,
        'today_total': today_total,
    }
    
    return render(request, 'core/timesheet_entry.html', context)


@login_required
def timesheet_edit_entry(request, entry_id):
    """
    View for employees to edit existing timesheet entries.
    """
    entry = get_object_or_404(TimesheetEntry, id=entry_id, employee=request.user)
    
    if request.method == 'POST':
        form = TimesheetEntryEditForm(request.POST, instance=entry, user=request.user)
        if form.is_valid():
            entry = form.save()
            messages.success(
                request,
                f'Timesheet entry for {entry.date} has been updated successfully.'
            )
            return redirect('timesheet_weekly_summary')
    else:
        form = TimesheetEntryEditForm(instance=entry, user=request.user)
    
    context = {
        'form': form,
        'entry': entry,
        'action': 'Edit',
    }
    
    return render(request, 'core/timesheet_entry_form.html', context)


@login_required
@require_POST
def timesheet_delete_entry(request, entry_id):
    """
    View for employees to delete timesheet entries.
    """
    entry = get_object_or_404(TimesheetEntry, id=entry_id, employee=request.user)
    
    entry_date = entry.date
    entry_hours = entry.hours
    entry_project = entry.project.name if entry.project else "No Project"
    
    entry.delete()
    
    messages.success(
        request,
        f'Timesheet entry for {entry_date} has been deleted. '
        f'({entry_hours}h - {entry_project})'
    )
    
    return redirect('timesheet_weekly_summary')


@login_required
def timesheet_weekly_summary(request):
    """
    View for employees to see weekly summary of timesheet entries.
    """
    from datetime import datetime, timedelta
    
    # Get week parameters from query string or default to current week
    week_str = request.GET.get('week', '')
    if week_str:
        try:
            selected_date = datetime.strptime(week_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()
    
    # Calculate start and end of week (Monday to Sunday)
    days_since_monday = selected_date.weekday()
    start_date = selected_date - timedelta(days=days_since_monday)
    end_date = start_date + timedelta(days=6)
    
    # Get weekly summary
    summary = TimesheetEntry.get_weekly_summary(
        request.user, start_date, end_date
    )
    
    # Generate daily breakdown
    daily_breakdown = []
    for i in range(7):
        current_day = start_date + timedelta(days=i)
        day_entries = TimesheetEntry.objects.filter(
            employee=request.user,
            date=current_day
        ).select_related('project').order_by('created_at')
        
        day_total = sum(entry.hours for entry in day_entries)
        
        daily_breakdown.append({
            'date': current_day,
            'day_name': current_day.strftime('%A'),
            'entries': day_entries,
            'total_hours': day_total,
            'is_today': current_day == date.today(),
        })
    
    # Calculate navigation dates
    prev_week = start_date - timedelta(days=7)
    next_week = start_date + timedelta(days=7)
    
    # Check if next week is in the future
    can_go_next = next_week <= date.today()
    
    context = {
        'summary': summary,
        'daily_breakdown': daily_breakdown,
        'start_date': start_date,
        'end_date': end_date,
        'prev_week': prev_week,
        'next_week': next_week,
        'can_go_next': can_go_next,
        'selected_week': start_date.strftime('%Y-%m-%d'),
    }
    
    return render(request, 'core/timesheet_weekly_summary.html', context)


@login_required
def timesheet_daily_entries(request, entry_date):
    """
    View to show all entries for a specific date.
    """
    try:
        target_date = datetime.strptime(entry_date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Invalid date format.')
        return redirect('timesheet_weekly_summary')
    
    entries = TimesheetEntry.objects.filter(
        employee=request.user,
        date=target_date
    ).select_related('project').order_by('created_at')
    
    # Calculate total hours for the day
    from django.db.models import Sum
    total_hours = entries.aggregate(total=Sum('hours'))['total'] or 0
    
    context = {
        'entries': entries,
        'target_date': target_date,
        'total_hours': total_hours,
    }
    
    return render(request, 'core/timesheet_daily_entries.html', context)


# ==================== PAYROLL/PAYSLIP VIEWS ====================

@login_required
@hr_required
def payslip_list(request):
    """HR view to list all payslips with filtering options."""
    payslips = Payslip.objects.select_related('employee').order_by('-year', '-month', 'employee__first_name')
    
    # Filter by employee
    employee_id = request.GET.get('employee')
    if employee_id:
        payslips = payslips.filter(employee_id=employee_id)
    
    # Filter by month/year
    month = request.GET.get('month')
    year = request.GET.get('year')
    if month:
        payslips = payslips.filter(month=month)
    if year:
        payslips = payslips.filter(year=year)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        payslips = payslips.filter(status=status)
    
    # Pagination
    paginator = Paginator(payslips, 20)
    page_number = request.GET.get('page')
    payslips = paginator.get_page(page_number)
    
    # Get filter options
    employees = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
    
    context = {
        'payslips': payslips,
        'employees': employees,
        'current_filters': {
            'employee': employee_id,
            'month': month,
            'year': year,
            'status': status,
        }
    }
    
    return render(request, 'core/payslip_list.html', context)


@login_required
@hr_required
def payslip_create(request):
    """HR view to create a new payslip."""
    if request.method == 'POST':
        form = PayslipForm(request.POST)
        if form.is_valid():
            payslip = form.save()
            messages.success(request, f'Payslip created successfully for {payslip.employee.get_full_name()}.')
            return redirect('payslip_detail', payslip_id=payslip.id)
    else:
        form = PayslipForm()
    
    context = {
        'form': form,
        'title': 'Create Payslip'
    }
    
    return render(request, 'core/payslip_form.html', context)


@login_required
def payslip_detail(request, payslip_id):
    """View payslip details - accessible by HR and the employee."""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    # Permission check: HR can view all, employees can only view their own
    if not (request.user.is_hr() or request.user.is_admin_role() or payslip.employee == request.user):
        messages.error(request, 'You do not have permission to view this payslip.')
        return redirect('dashboard')
    
    context = {
        'payslip': payslip,
        'can_edit': request.user.is_hr() or request.user.is_admin_role(),
    }
    
    return render(request, 'core/payslip_detail.html', context)


@login_required
@hr_required
def payslip_edit(request, payslip_id):
    """HR view to edit an existing payslip."""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    if request.method == 'POST':
        form = PayslipForm(request.POST, instance=payslip)
        if form.is_valid():
            payslip = form.save()
            messages.success(request, f'Payslip updated successfully for {payslip.employee.get_full_name()}.')
            return redirect('payslip_detail', payslip_id=payslip.id)
    else:
        form = PayslipForm(instance=payslip)
    
    context = {
        'form': form,
        'payslip': payslip,
        'title': f'Edit Payslip - {payslip.employee.get_full_name()}'
    }
    
    return render(request, 'core/payslip_form.html', context)


@login_required
@hr_required
def payslip_delete(request, payslip_id):
    """HR view to delete a payslip."""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    if request.method == 'POST':
        employee_name = payslip.employee.get_full_name()
        payslip.delete()
        messages.success(request, f'Payslip deleted successfully for {employee_name}.')
        return redirect('payslip_list')
    
    context = {
        'payslip': payslip,
    }
    
    return render(request, 'core/payslip_delete_confirm.html', context)


@login_required
def my_payslips(request):
    """Employee view to see their own payslips."""
    payslips = Payslip.objects.filter(employee=request.user).order_by('-year', '-month')
    
    # Pagination
    paginator = Paginator(payslips, 12)  # 12 payslips per page (1 year)
    page_number = request.GET.get('page')
    payslips = paginator.get_page(page_number)
    
    context = {
        'payslips': payslips,
    }
    
    return render(request, 'core/my_payslips.html', context)


@login_required
@hr_required
def payslip_bulk_upload(request):
    """HR view to bulk upload payslips via CSV."""
    if request.method == 'POST':
        form = PayslipBulkUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            
            try:
                import csv
                import io
                from django.db import transaction
                
                # Read CSV file
                file_data = csv_file.read().decode('utf-8')
                reader = csv.DictReader(io.StringIO(file_data))
                
                created_count = 0
                errors = []
                
                with transaction.atomic():
                    for row_num, row in enumerate(reader, start=1):
                        try:
                            # Get employee by username or email
                            employee_identifier = row.get('employee_username') or row.get('employee_email')
                            if not employee_identifier:
                                errors.append(f"Row {row_num}: Missing employee identifier")
                                continue
                            
                            try:
                                if '@' in employee_identifier:
                                    employee = User.objects.get(email=employee_identifier, is_active=True)
                                else:
                                    employee = User.objects.get(username=employee_identifier, is_active=True)
                            except User.DoesNotExist:
                                errors.append(f"Row {row_num}: Employee not found: {employee_identifier}")
                                continue
                            
                            # Create payslip
                            payslip_data = {
                                'employee': employee,
                                'month': int(row.get('month', 0)),
                                'year': int(row.get('year', 0)),
                                'basic': float(row.get('basic', 0)),
                                'hra': float(row.get('hra', 0)),
                                'allowances': float(row.get('allowances', 0)),
                                'overtime_hours': float(row.get('overtime_hours', 0)),
                                'overtime_pay': float(row.get('overtime_pay', 0)),
                                'bonus': float(row.get('bonus', 0)),
                                'deductions': float(row.get('deductions', 0)),
                                'income_tax': float(row.get('income_tax', 0)),
                                'provident_fund': float(row.get('provident_fund', 0)),
                                'professional_tax': float(row.get('professional_tax', 0)),
                                'status': row.get('status', 'DRAFT'),
                                'notes': row.get('notes', ''),
                            }
                            
                            # Handle pay_date
                            pay_date_str = row.get('pay_date')
                            if pay_date_str:
                                from datetime import datetime
                                payslip_data['pay_date'] = datetime.strptime(pay_date_str, '%Y-%m-%d').date()
                            
                            # Check for existing payslip
                            existing = Payslip.objects.filter(
                                employee=employee,
                                month=payslip_data['month'],
                                year=payslip_data['year']
                            ).first()
                            
                            if existing:
                                errors.append(f"Row {row_num}: Payslip already exists for {employee.get_full_name()}")
                                continue
                            
                            # Create payslip
                            Payslip.objects.create(**payslip_data)
                            created_count += 1
                            
                        except (ValueError, KeyError) as e:
                            errors.append(f"Row {row_num}: Invalid data - {str(e)}")
                            continue
                
                if created_count > 0:
                    messages.success(request, f'Successfully created {created_count} payslips.')
                
                if errors:
                    error_message = f'Errors encountered:\\n' + '\\n'.join(errors[:10])  # Show first 10 errors
                    if len(errors) > 10:
                        error_message += f'\\n... and {len(errors) - 10} more errors.'
                    messages.warning(request, error_message)
                
                if created_count > 0:
                    return redirect('payslip_list')
                    
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
    else:
        form = PayslipBulkUploadForm()
    
    context = {
        'form': form,
        'csv_template_headers': [
            'employee_username', 'employee_email', 'month', 'year', 'basic', 'hra', 
            'allowances', 'overtime_hours', 'overtime_pay', 'bonus', 'deductions', 
            'income_tax', 'provident_fund', 'professional_tax', 'pay_date', 'status', 'notes'
        ]
    }
    
    return render(request, 'core/payslip_bulk_upload.html', context)
