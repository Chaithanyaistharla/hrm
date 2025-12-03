from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth.views import LogoutView
from . import views

def home_redirect(request):
    """Redirect root URL to login or dashboard based on auth status"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/employee/', views.dashboard_employee_view, name='dashboard_employee'),
    path('dashboard/hr/', views.dashboard_hr_view, name='dashboard_hr'),
    path('profile/', views.profile_view, name='profile'),
    path('directory/', views.org_directory, name='org_directory'),
    
    # Employee management URLs
    path('employee/profile/', views.employee_profile_view, name='employee_profile'),
    path('employee/profile/edit/', views.employee_profile_edit_view, name='employee_profile_edit'),
    path('employee/directory/', views.employee_directory_view, name='employee_directory'),
    path('employee/<int:user_id>/', views.employee_detail_view, name='employee_detail'),
    
    # Test URLs for role-based access control
    path('test/hr/', views.hr_only_view, name='hr_test'),
    path('test/admin/', views.admin_only_view, name='admin_test'),
    
    # Attendance management
    path('attendance/', views.attendance_page, name='attendance_page'),
    path('attendance/dashboard/', views.employee_attendance_dashboard, name='employee_attendance_dashboard'),
    path('attendance/team/', views.team_attendance_view, name='team_attendance_view'),
    
    # Attendance API endpoints
    path('attendance/clock-in/', views.clock_in_api, name='attendance_clock_in'),
    path('attendance/clock-out/', views.clock_out_api, name='attendance_clock_out'),
    path('attendance/status/', views.attendance_status_api, name='attendance_status'),
    
    # Leave Management
    path('leave/apply/', views.apply_leave, name='apply_leave'),
    path('leave/my-leaves/', views.my_leaves, name='my_leaves'),
    path('leave/team/', views.manage_team_leaves, name='manage_team_leaves'),  # Legacy redirect
    path('leave/manager/pending/', views.manager_pending_leaves, name='manager_pending_leaves'),
    path('leave/hr/all/', views.hr_all_leaves, name='hr_all_leaves'),
    path('leave/approve/<int:leave_id>/', views.approve_leave, name='approve_leave'),
    path('leave/reject/<int:leave_id>/', views.reject_leave, name='reject_leave'),
    
    # Project Management
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:project_id>/delete/', views.project_delete, name='project_delete'),
    path('projects/<int:project_id>/add-member/', views.project_add_member, name='project_add_member'),
    path('projects/<int:project_id>/member/<int:member_id>/edit/', views.project_edit_member, name='project_edit_member'),
    path('projects/<int:project_id>/member/<int:member_id>/remove/', views.project_remove_member, name='project_remove_member'),
    path('my-projects/', views.my_projects, name='my_projects'),
    
    # Timesheet Management
    path('timesheets/', views.timesheet_entry, name='timesheet_entry'),
    path('timesheets/weekly/', views.timesheet_weekly_summary, name='timesheet_weekly_summary'),
    path('timesheets/daily/<str:date>/', views.timesheet_daily_entries, name='timesheet_daily_entries'),
    path('timesheets/edit/<int:entry_id>/', views.timesheet_edit_entry, name='timesheet_edit_entry'),
    path('timesheets/delete/<int:entry_id>/', views.timesheet_delete_entry, name='timesheet_delete_entry'),
    
    path('', home_redirect, name='home'),
]