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
    
    path('', home_redirect, name='home'),
]