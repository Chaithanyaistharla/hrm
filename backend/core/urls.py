from django.urls import path
from django.shortcuts import redirect
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
    path('profile/', views.profile_view, name='profile'),
    
    # Employee management URLs
    path('employee/profile/', views.employee_profile_view, name='employee_profile'),
    path('employee/profile/edit/', views.employee_profile_edit_view, name='employee_profile_edit'),
    path('employee/directory/', views.employee_directory_view, name='employee_directory'),
    path('employee/<int:user_id>/', views.employee_detail_view, name='employee_detail'),
    
    path('', home_redirect, name='home'),
]